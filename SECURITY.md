# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

We take the security of LogEverything seriously. If you believe you have found a security vulnerability, please report it to us as described below.

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via:

1. **GitHub Security Advisories**: Go to the [Security tab](https://github.com/RamishSiddiqui/logeverything/security/advisories) and click "Report a vulnerability"
2. **Email**: Send a detailed description to [INSERT SECURITY EMAIL]

You should receive a response within 48 hours. If for some reason you do not, please follow up via the same channel.

## What to Include

When reporting a vulnerability, please include:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Any suggested fixes (if applicable)
- Your contact information for follow-up questions

## Response Process

1. **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
2. **Verification**: We will verify the vulnerability and assess its severity
3. **Fix Development**: We will develop and test a fix
4. **Release**: A patched version will be released
5. **Disclosure**: After the fix is released, we will publicly acknowledge your contribution (unless you prefer to remain anonymous)

## Security Best Practices

When using LogEverything in production:

- Keep the library updated to the latest version
- Review and configure logging levels appropriately for your environment
- Be cautious about logging sensitive data (passwords, tokens, PII)
- Use the `quiet()` context manager to suppress logging in sensitive code paths
- Review transport configurations when shipping logs to remote endpoints
