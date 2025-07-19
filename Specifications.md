# Smart Home Device Communications Protocol (SHDC) v1.0 

## 1. Overview

This protocol defines a secure communication system between low-power **Sensors** a#### 7.6.1 `HUB_DISCOVERY_REQ` (0x00)

**Sent by Sensor as a UDP Broadcast or Multicast**

- Destination: `255.255.255.255:56700` or `239.255.0.1:56700` (official SHDC port)
- Not encrypted, but signed using the sensor's Ed25519 keyocal **Security Hub**. It supports encrypted **unicast** messages (sensor → hub), **broadcasts** (hub → sensors), and **key management** in a closed, trusted network.

---

## 2. Roles

- **Sensor**: Embedded node sending event/status data.
- **Hub**: Local control node handling routing and authentication.

---

## 3. Transport

- **Layer**: UDP preferred; TCP optional fallback.
- **Port**: 56700 (official SHDC port)
- **Broadcasts**: Multicast IP (`239.255.0.1:56700`) or Layer 2.
- **Max Packet Size**: 512 bytes for compatibility with embedded devices.
- **IPv4/IPv6** supported.

### 3.1 Port Assignment

- **Standard Port**: 56700/UDP (primary)
- **Fallback Port**: 56700/TCP (for reliability-critical operations)
- **Port Range**: 56700-56709 reserved for SHDC protocol variants
- **Discovery**: Hub listens on 56700/UDP for discovery broadcasts
- **Communication**: All unicast and multicast traffic uses port 56700

---

## 4. Security Model

### Identity & Keys

| Device  | Key Type         | Purpose                     |
|---------|------------------|-----------------------------|
| Sensor  | Ed25519 keypair  | Identity, signing           |
| Hub     | Ed25519 keypair  | Signing (optional)          |
| Both    | AES-256-GCM      | Session encryption          |
| Hub     | AES-256 group key| Broadcast encryption        |

All keys are provisioned during install or via a secure join handshake.

---

## 5. Message Types

| Code  | Direction     | Name               | Description                  |
|-------|---------------|--------------------|------------------------------|
| 0x01  | Sensor → Hub  | `EVENT_REPORT`     | Event or status message      |
| 0x02  | Sensor → Hub  | `JOIN_REQUEST`     | Join handshake initiation    |
| 0x03  | Hub → Sensor  | `JOIN_RESPONSE`    | Response with keys/config    |
| 0x04  | Hub → Sensor  | `BROADCAST_COMMAND`| Broadcasted command          |
| 0x05  | Any           | `KEY_ROTATION`     | Key update                   |

---

## 6. Packet Format

### General Layout

```
+------------------+--------------------+---------------------+
| Header (12 B)    | Encrypted Payload  | Signature (64 B)    |
+------------------+--------------------+---------------------+
```

### Header Fields (12 bytes)

| Field      | Size | Description                     |
|------------|------|---------------------------------|
| Type       | 1 B  | Message type code               |
| Sensor ID  | 4 B  | Unique device identifier        |
| Timestamp  | 4 B  | UNIX time                       |
| Nonce      | 3 B  | Random nonce for replay defense |

### Signature (64 bytes)

- Algorithm: `Ed25519`
- Covers: `Header + Encrypted Payload`

---

## 7. Message Definitions

### 7.1 `EVENT_REPORT` (0x01)

Sensor reports event to hub.

**Encrypted Payload (AES-GCM):**

| Field        | Size    | Description          |
|--------------|---------|----------------------|
| Event Type   | 1 B     | E.g. motion = 0x01   |
| Data Length  | 1 B     | Size of `Data` field |
| Data         | N bytes | Sensor-specific info |

---

### 7.2 `JOIN_REQUEST` (0x02)

Initial join request from sensor.

**Unencrypted Payload:**

| Field         | Size     | Description               |
|---------------|----------|---------------------------|
| Public Key    | 32 B     | Sensor’s Ed25519 pubkey   |
| Device Info   | Optional | Text/model info           |

---

### 7.3 `JOIN_RESPONSE` (0x03)

Hub responds with session keys.

**Payload (encrypted with sensor’s pubkey):**

| Field             | Size     | Description                  |
|------------------|----------|------------------------------|
| Assigned ID      | 4 B      | Unique numeric ID for sensor |
| Session Key      | 32 B     | AES-GCM key                  |
| Broadcast Key ID | 1 B      | Group key version/tag        |

---

### 7.4 `BROADCAST_COMMAND` (0x04)

Hub sends command to all sensors.

**Encrypted Payload (group AES-GCM key):**

| Field             | Size    | Description                 |
|------------------|---------|-----------------------------|
| Command Type     | 1 B     | E.g. lockdown = 0x01        |
| Command Data     | N B     | Depends on command          |
| Broadcast Key ID | 1 B     | Used to track key versions  |

---

### 7.5 `KEY_ROTATION` (0x05)
### 7.6 `HUB_DISCOVERY_REQ` and `HUB_DISCOVERY_RESP` (0x00 / 0x06)

#### Purpose

Allows a sensor to discover a hub on the local network using UDP broadcast or multicast. Used when a sensor does not know the hub's IP but has its own keys.

#### Message Types

| Code  | Direction     | Name                  | Description                     |
|-------|---------------|-----------------------|---------------------------------|
| 0x00  | Sensor → Hub  | `HUB_DISCOVERY_REQ`    | Broadcast to discover hub       |
| 0x06  | Hub → Sensor  | `HUB_DISCOVERY_RESP`   | Unicast response with identity  |

#### 7.6.1 `HUB_DISCOVERY_REQ` (0x00)

**Sent by Sensor as a UDP Broadcast or Multicast**

- Destination: `255.255.255.255:56700` or `239.255.0.1:56700`
- Not encrypted, but signed using the sensor’s Ed25519 key

**Header:**
```
Type:        0x00
Sensor ID:   0x00000000 (unassigned)
Timestamp:   UNIX time
Nonce:       3 bytes random
```

**Payload:**
| Field            | Size | Description                    |
|------------------|------|--------------------------------|
| Public Key       | 32 B | Sensor’s Ed25519 public key    |
| Device Info      | Var. | (Optional) Textual identifier  |

**Signature:** 64 B, over `Header + Payload`

#### 7.6.2 `HUB_DISCOVERY_RESP` (0x06)

**Sent by Hub as a Unicast UDP Response**

- Sent to sender’s IP:port
- Signed by hub

**Header:**
```
Type:        0x06
Sensor ID:   Echoed or 0
Timestamp:   UNIX time
Nonce:       Echoed or new
```

**Payload:**
| Field            | Size | Description                     |
|------------------|------|---------------------------------|
| Hub ID           | 4 B  | Unique hub identifier           |
| Hub Public Key   | 32 B | Hub’s Ed25519 public key        |
| Capabilities     | Var. | Optional (e.g. version info)    |

**Signature:** 64 B, Ed25519 over `Header + Payload`

#### Sensor Behavior

1. Broadcasts `HUB_DISCOVERY_REQ` on boot.
2. Listens for 1s for responses.
3. Validates hub signature.
4. Selects and stores valid hub IP/public key.
5. Proceeds to `JOIN_REQUEST`.

#### Retry and Timeout

- Retry every 5s (exponential backoff up to 30s)
- Timeout after 5 min, enter idle mode

#### Security Notes

- All messages are signed.
- Discovery is verified but not encrypted.
- Can be extended to use PKI/certificates.


Update session or group keys.

**Encrypted Payload:**

| Field          | Size | Description             |
|----------------|------|-------------------------|
| New AES Key    | 32 B | New encryption key      |
| Valid From     | 4 B  | UNIX time for activation|

---

## 8. Replay Protection

- Timestamps must be within ±30 seconds of hub’s clock.
- Nonce values are cached for short-term detection of duplicates.
- Messages with reused `(Sensor ID + Nonce)` are discarded.

---

## 9. Broadcast Logic

- **Hub** uses AES-GCM encrypted messages to `239.255.0.1`.
- Sensors maintain the latest broadcast key (rotated periodically).
- Sensors discard commands with old timestamps or unknown key IDs.

---

## 10. Implementation Notes

- Use `libsodium`, `NaCl`, or `wolfSSL` for crypto.
- Store sensor keys in secure flash or TPM if available.
- Hub should sync clock (e.g., via NTP or GPS) regularly.
- All messages are fixed format for parsing simplicity.

---

## 11. Example: Motion Event

```
Header:
- Type: 0x01
- Sensor ID: 0xAABBCCDD
- Timestamp: 1723456789
- Nonce: 0xC7F1A2

Encrypted Payload:
- Event Type: 0x01 (Motion)
- Data Length: 0x00 (none)

Signature: Ed25519(Header + Encrypted Payload)
```

---

## 12. Key Rotation Recommendation

- **Session Key**: Every 24 hours
- **Broadcast Key**: Every 15 minutes or after reboot
- **Rekey messages** are sent individually encrypted using `KEY_ROTATION`
