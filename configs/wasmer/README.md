# Wasmer Reconciled Configuration (4 Physical Applications)

This directory contains the reconciled configurations for the 4 authentic physical Wasmer applications under the V13 architecture:

## 1. edgetunnel-us-la
- Application Name: edgetunnel-us-la
- App ID: da_KN4IZtyUPwOL
- Deployment ID: dav_RjPIgtzuJwQ9
- Region: us-losa1 (Los Angeles, US)
- Domain: w-la.ruoyemu.asia (CNAME: edgetunnel-us-la.wasmer.app)
- Target Egress: AS20473 Choopa / Constant Company LLC
- Config: edgetunnel-us-la.yaml (or edgetunnel-us-la/app.yaml)

## 2. edgetunnel-fr
- Application Name: edgetunnel-fr
- App ID: da_2J7IAtxU5d1P
- Deployment ID: dav_2VbInozrPwQz
- Region: fr-roub1 (Gravelines / Paris, France)
- Domain: w-fr.ruoyemu.asia (CNAME: edgetunnel-fr.wasmer.app)
- Target Egress: AS16276 OVH
- Config: edgetunnel-fr.yaml (or edgetunnel-fr/app.yaml)

## 3. edgetunnel-us-east
- Application Name: edgetunnel-us-east
- App ID: da_2OPIqt7U4pbr
- Deployment ID: dav_6N1Ip1znJwA1
- Region: us-ashburn (Ashburn, US)
- Domain: w-east.ruoyemu.asia (CNAME: edgetunnel-us-east.wasmer.app)
- Target Egress: AS213230 Hetzner
- Config: edgetunnel-us-east.yaml (or edgetunnel-us-east/app.yaml)

## 4. edgetunnel-us-west
- Application Name: edgetunnel-us-west (vless-ws-test)
- App ID: da_K53IxtPUOdjp
- Deployment ID: dav_8V7IzpyjPlnE
- Region: us-hillsboro (Hillsboro, Oregon, US)
- Domain: w-us.ruoyemu.asia (CNAME: vless-ws-test.wasmer.app)
- Target Egress: AS212317 Hetzner
- Config: edgetunnel-us-west.yaml (or edgetunnel-us-west/app.yaml)

## Enforcement
- Total physical applications: exactly 4.
- Total published proxy nodes limit: <= 4.
- Fictional/alias nodes (such as the duplicate w-fr.ruoyemu.asia path alias): strictly eliminated.
