# Digital Signature

As of February 18, 2026, all official executables distributed by PaulNeja (PN Security) are digitally signed using a proprietary code-signing certificate.

The digital signature serves the following purposes:

Verify the integrity of the executable file.

Allow confirmation that the binary has not been modified after compilation.

Associate the executable with a specific cryptographic identity.

Provide traceability for official builds.

Enable manual validation using tools such as signtool or Windows file properties.

Scope of the Signature

The digital signature:

Does not modify the program’s functionality.

Does not add additional dependencies.

Does not require an Internet connection for basic signature validation.

Does not prevent execution on systems where the certificate is not installed.

The software functions correctly even if the certificate is not installed on the user’s system.

Certificate installation is completely optional.

# Certificate Nature

The certificate used is a self-signed code-signing certificate.

This means:

It is not issued by a commercial Certificate Authority.

It does not automatically eliminate SmartScreen warnings on external systems.

Its primary purpose is to guarantee integrity and consistency of official builds.

The private key associated with the certificate is not published or distributed.

This repository includes only the public certificate (.cer).

Optional Certificate Installation on Windows

Installing the certificate allows Windows to identify the signed executable by displaying the publisher name instead of “Unknown Publisher.”

# Important clarification: Installation is not required to use the software.

Graphical Method (Recommended)

Download the .cer file included in the repository.

Double-click the file.

Select “Install Certificate.”

Choose “Current User” or “Local Machine” (Local Machine recommended).

Select “Place all certificates in the following store.”

Choose “Trusted Root Certification Authorities.”

Confirm installation.

System confirmation may be required.

Alternative Manual Method

The certificate may also be installed via command line using system tools, if the user has advanced knowledge.

# Signature Verification

To manually verify the digital signature of an executable:

Right-click the file.

Select “Properties.”

Go to the “Digital Signatures” tab.

Select the corresponding signature and view details.

It may also be verified using:

signtool verify /pa SentinelDesk.exe

Security Considerations

Installing a code-signing certificate implies trusting the identity associated with that certificate.

# The user must:

Verify the fingerprint published in the repository.

Confirm that the certificate originates from the official source.

Install only certificates downloaded from the official repository.

Installing unofficial certificates may compromise system security.

# Signing Policy

All official executables distributed from February 18, 2026 onward are digitally signed.

The absence of a digital signature may indicate:

Unofficial compilation.

Modified file.

Unauthorized distribution.

# Official Certificate Fingerprint

Code Signing Certificate — PaulNeja (PN Security)
Valid as of February 18, 2026

# SHA1
8F61E94560D1B2E621E7DC001F3742E472EAA9EA

# SHA256
95BF563120D87ED73CC000CB35BB30173638C4014AA3388DC6BB70CB021EC536
