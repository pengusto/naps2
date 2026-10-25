// Copyright (c) 2026 Pengusto. MIT; see ../LICENSE-tools.txt.
// Disposable offline-test key. Never use this seed as the release signing key.
import Foundation
import CryptoKit

guard CommandLine.arguments.count == 2 else { exit(2) }
let destination = URL(fileURLWithPath: CommandLine.arguments[1])
guard !FileManager.default.fileExists(atPath: destination.path) else { exit(3) }
let key = Curve25519.Signing.PrivateKey()
try (key.rawRepresentation.base64EncodedString() + "\n").write(to: destination, atomically: true, encoding: .utf8)
try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: destination.path)
try (key.publicKey.rawRepresentation.base64EncodedString() + "\n").write(
    to: URL(fileURLWithPath: destination.path + ".pub"), atomically: true, encoding: .utf8)
