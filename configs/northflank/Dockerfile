FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum* ./
RUN go mod download || true
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/gateway .

FROM alpine:3.20
RUN apk add --no-cache ca-certificates
WORKDIR /
COPY --from=builder /app/gateway /gateway
EXPOSE 8080 8443
ENV PORT=8443
ENTRYPOINT ["/gateway"]
