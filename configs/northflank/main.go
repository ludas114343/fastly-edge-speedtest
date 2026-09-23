package main

import (
	"crypto/subtle"
	"encoding/base64"
	"encoding/binary"
	"log"
	"net"
	"net/http"
	"os"
	"strconv"
	"strings"

	"github.com/gorilla/websocket"
)

var (
	targetUUID []byte
	upgrader   = websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool { return true },
	}
)

func init() {
	uuidStr := os.Getenv("UUID")
	if uuidStr == "" {
		uuidStr = "6d84f981-22fb-4e78-9e56-59b48b59d9c2"
	}
	raw := strings.ReplaceAll(uuidStr, "-", "")
	var err error
	targetUUID, err = hexDecode(raw)
	if err != nil || len(targetUUID) != 16 {
		log.Fatalf("Invalid UUID: %v", err)
	}
}

func hexDecode(s string) ([]byte, error) {
	dst := make([]byte, len(s)/2)
	for i := 0; i < len(dst); i++ {
		b, err := strconv.ParseUint(s[i*2:i*2+2], 16, 8)
		if err != nil {
			return nil, err
		}
		dst[i] = byte(b)
	}
	return dst, nil
}

func handleCamouflage(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("<!DOCTYPE html><html><head><title>Welcome to nginx!</title></head><body><h1>Welcome to nginx!</h1><p>Northflank Edge Gateway Operational.</p></body></html>"))
}

func handleVlessWS(w http.ResponseWriter, r *http.Request) {
	if strings.ToLower(r.Header.Get("Upgrade")) != "websocket" {
		handleCamouflage(w, r)
		return
	}

	wsConn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		return
	}
	defer wsConn.Close()

	var firstPacket []byte

	// Check 0-RTT Early Data from Sec-WebSocket-Protocol
	secProto := r.Header.Get("Sec-WebSocket-Protocol")
	if secProto != "" {
		if decoded, err := base64.RawURLEncoding.DecodeString(secProto); err == nil && len(decoded) >= 18 {
			firstPacket = decoded
		}
	}

	// If no early data, read first frame from WebSocket
	if len(firstPacket) == 0 {
		_, msg, err := wsConn.ReadMessage()
		if err != nil || len(msg) < 18 {
			return
		}
		firstPacket = msg
	}

	// 1. Parse VLESS Protocol Header
	version := firstPacket[0]
	incomingUUID := firstPacket[1:17]
	if subtle.ConstantTimeCompare(incomingUUID, targetUUID) != 1 {
		return
	}

	optLen := int(firstPacket[17])
	cursor := 18 + optLen
	if len(firstPacket) < cursor+4 {
		return
	}

	command := firstPacket[cursor]
	cursor++
	if command != 1 { // 1 = TCP
		return
	}

	port := binary.BigEndian.Uint16(firstPacket[cursor : cursor+2])
	cursor += 2

	addrType := firstPacket[cursor]
	cursor++

	var targetHost string
	switch addrType {
	case 1: // IPv4
		if len(firstPacket) < cursor+4 {
			return
		}
		targetHost = net.IP(firstPacket[cursor : cursor+4]).String()
		cursor += 4
	case 2: // Domain
		domainLen := int(firstPacket[cursor])
		cursor++
		if len(firstPacket) < cursor+domainLen {
			return
		}
		targetHost = string(firstPacket[cursor : cursor+domainLen])
		cursor += domainLen
	case 3: // IPv6
		if len(firstPacket) < cursor+16 {
			return
		}
		targetHost = net.IP(firstPacket[cursor : cursor+16]).String()
		cursor += 16
	default:
		return
	}

	initialPayload := firstPacket[cursor:]

	// 2. Direct TCP Dial via net.Dialer
	destAddr := net.JoinHostPort(targetHost, strconv.Itoa(int(port)))
	remoteConn, err := net.Dial("tcp", destAddr)
	if err != nil {
		return
	}
	defer remoteConn.Close()

	// 3. Send VLESS Response Header back to client
	if err := wsConn.WriteMessage(websocket.BinaryMessage, []byte{version, 0x00}); err != nil {
		return
	}

	// 4. Flush initial payload to target
	if len(initialPayload) > 0 {
		if _, err := remoteConn.Write(initialPayload); err != nil {
			return
		}
	}

	// 5. Full-duplex bidirectional streaming
	done := make(chan struct{}, 2)

	// Remote TCP -> WebSocket
	go func() {
		buf := make([]byte, 32768)
		for {
			n, err := remoteConn.Read(buf)
			if n > 0 {
				if wErr := wsConn.WriteMessage(websocket.BinaryMessage, buf[:n]); wErr != nil {
					break
				}
			}
			if err != nil {
				break
			}
		}
		done <- struct{}{}
	}()

	// WebSocket -> Remote TCP
	go func() {
		for {
			_, msg, err := wsConn.ReadMessage()
			if len(msg) > 0 {
				if _, wErr := remoteConn.Write(msg); wErr != nil {
					break
				}
			}
			if err != nil {
				break
			}
		}
		done <- struct{}{}
	}()

	<-done
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	http.HandleFunc("/", handleVlessWS)
	http.HandleFunc("/ws", handleVlessWS)
	log.Printf("[Northflank] Go VLESS Direct Gateway listening on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
