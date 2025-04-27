# Cryptography and Network Security <!-- omit in toc -->

# Lab 6: Hybrid/Envelope Encryption using RSA and AES <!-- omit in toc -->

## Introduction

This lab demonstrates hybrid/envelope encryption, a fundamental cryptographic construction that uses multiple keys to secure data. In this implementation, we combine RSA for key encryption and AES for data encryption.

### What is Envelope Encryption?

Envelope encryption is a cryptographic system that secures messages using two keys:

1. **Long-term Key**: A static RSA key pair, referred to as the Key Encryption Key (KEK).
2. **Per-message Key**: A unique AES key, known as the Data Encryption Key (DEK), generated for each message.

Construction process:
1. Generate a random AES key (DEK) for the message.
2. Encrypt the message using the DEK and an initialization vector (IV), producing the ciphertext.
3. Encrypt the DEK using the RSA KEK, producing the encrypted DEK (encryptedDEK).
4. Combine the encrypted DEK, IV, and ciphertext into a single envelope structure: `(encryptedDEK, IV, ciphertext)`.

Here:
- The DEK (AES key) enables efficient per-message encryption.
- The KEK (RSA key pair) securely protects the DEK.
- The envelope format `(encryptedDEK, IV, ciphertext)` ensures secure storage and transmission.

This approach balances security and efficiency by using a unique DEK for each message, safeguarded by a long-term KEK.

### Key Benefits

1. **Protecting data keys**: When you encrypt a data key, you don't have to worry about storing the encrypted data key, because the data key is inherently protected by encryption. You can safely store the encrypted data key alongside the encrypted data.

2. **Encrypting the same data under multiple keys**: Encryption operations can be time consuming, particularly when the data being encrypted are large objects. Instead of re-encrypting raw data multiple times with different keys, you can re-encrypt only the data keys that protect the raw data.

3. **Combining the strengths of multiple algorithms**: In general, symmetric key algorithms are faster and produce smaller ciphertexts than public key algorithms. But public key algorithms provide inherent separation of roles and easier key management. Envelope encryption lets you combine the strengths of each strategy.


Source: [AWS KMS Cryptographic Details](https://docs.aws.amazon.com/kms/latest/developerguide/kms-cryptography.html)

## Network Topology

The network topology for this lab is given in the image below.

<p align="center">
  <img src="../img/envelope_encryption_topology.png" width="400px" height="auto"/>
</p>

## Challenge Description

Your task is to recover a `flag` that has been secured using hybrid/envelope encryption. You will be provided with a challenge file (`challenge.txt` located in your home directory) containing:

- RSA public exponent (e)
- One prime factor (p) of the RSA modulus
- Encrypted AES key
- Initialization vector (IV)
- Ciphertext

The challenge involves:

1. Reconstructing the RSA private key:
   - You have one prime factor (p)
   - Calculate the second prime factor (q) using n
   - Derive the private exponent (d)
   - Construct the complete RSA private key

2. Decrypting the envelope:
   - Use the reconstructed private key to decrypt the AES key
   - Use the decrypted AES key and provided IV to decrypt the ciphertext and recover your `flag`

## Hints

1. Check relevant parts of the source code used to prepare this challenge: [`code/envelope_encryption/`](../code/envelope_encryption/)
2. Python [cryptography library](https://cryptography.io) can help with both RSA key reconstruction and decryption. In particular, the following code snippet is quite relevant:

    ```python
    private_key = rsa.RSAPrivateNumbers(
        p=p,
        q=q,
        d=d,
        dmp1=pow(e, -1, p-1),
        dmq1=pow(e, -1, q-1),
        iqmp=pow(q, -1, p),
        public_numbers=rsa.RSAPublicNumbers(e=e, n=n)
    ).private_key(default_backend())
    ```
3. Some parts of the challenge data are base64-encoded, while others are in hexadecimal—make sure to decode them properly (refer to the source code for details).