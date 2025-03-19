# Cryptography and Network Security <!-- omit in toc -->

# Lab 2: When Deterministic Encryption Fails <!-- omit in toc -->

## Introduction

Electronic Code Book (ECB) mode demonstrates how deterministic encryption can fail:
- Same plaintext blocks produce identical ciphertext blocks
- Patterns in plaintext remain visible in ciphertext
- No randomization between blocks

<br/>
<p align="center">
<img src="../img/ecb.png" alt="ECB encryption" width="400px" height="auto"/>
<br>
</p>
In this exercise, we will see that this encryption method does not ensure message confidentiality (_confidentiality_) even when using a secure cipher (e.g., AES).

<br/>
<p align="center">
<img src="../img/tux_ecb.png" alt="Deterministic encryption" width="400px" height="auto"/>
</p>

## Network Topology

The network topology for this lab is given in the image below. The server implements a simple REST API service providing ECB mode encryption:

<p align="center">
  <img src="../img/lab_topology_server_only.png" width="400px" height="auto"/>
</p>

## Challenge Description

Your task: exploit ECB mode's deterministic nature to recover the flag. The server encrypts data (and flag) in ECB mode, making it vulnerable to pattern analysis.

> **Chosen-Plaintext Attack (CPA)**
>
> Attack steps:
>   1. Submit carefully crafted plaintexts to observe patterns
>   2. Analyze block boundaries
>   3. Use pattern matching to recover the flag

## Hints

1. Try `ssh -L 80:server:80 your_name@your_attacker_IP` and check the REST API documentation using `http://localhost/docs`
    > IMPORTANT: Understand the details of the REST API endpoints (check with the instructor if in doubt).
2. Remember: ECB encrypts each block independently implying `identical plaintext blocks = identical ciphertext blocks`
3. The `flag` consists of characters from the following set: `abcdefghijklmnopqrstuvwxyz0123456789{}!@#$%^&*`
4. Consult the source code check the source code in [`code/ecb`](../code/ecb)
