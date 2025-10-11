# 🔒 Security Guide - AI Chat Interface

## ⚠️ Critical Security Requirements

### 🚨 Immediate Actions Required

If you've just cloned this repository or are setting up for the first time:

1. **Verify `.env` is NOT in Git**
   ```bash
   git ls-files | grep .env
   # Should only show .env.example, NOT .env
   ```

2. **Create Your `.env` File**
   ```bash
   cp .env.example .env
   ```

3. **Generate Strong Credentials**
   ```bash
   # Generate JWT Secret
   python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

   # Generate Admin Password (use a password manager!)
   python -c "import secrets; import string; chars = string.ascii_letters + string.digits + string.punctuation; print('ADMIN_PASSWORD=' + ''.join(secrets.choice(chars) for _ in range(20)))"
   ```

4. **Set Supabase Credentials**
   - Go to your Supabase project: https://app.supabase.com
   - Navigate to Settings → API
   - Copy your `URL` and `anon` key
   - Add to `.env` file

## 🛡️ Security Best Practices

### Environment Variables

#### ✅ DO:
- Store ALL credentials in `.env` file
- Use strong, randomly generated secrets
- Rotate credentials regularly (every 90 days)
- Keep `.env` in `.gitignore`
- Use different credentials for dev/staging/production

#### ❌ DON'T:
- Hardcode credentials in source code
- Commit `.env` to Git
- Share `.env` files via email/Slack
- Use default or weak passwords
- Reuse credentials across environments

### Password Requirements

#### Admin Password
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, and special characters
- No dictionary words or common patterns
- Change immediately after first deployment

#### JWT Secret Key
- Minimum 32 characters
- Randomly generated (use `secrets.token_urlsafe(32)`)
- Never use default values
- Rotate every 90 days

### Database Security

#### Supabase
- Use Row Level Security (RLS) policies
- Never expose `service_role` key in frontend
- Use `anon` key for client-side operations
- Enable MFA for Supabase account
- Regularly review database logs

#### Connection Strings
- Never hardcode database passwords
- Use environment variables exclusively
- Enable SSL/TLS for all connections
- Restrict database access by IP when possible

## 🔐 Credential Rotation

### When to Rotate

Rotate credentials immediately if:
- Credentials were committed to Git (even if removed later)
- Credentials were shared insecurely
- A team member with access leaves
- Suspicious activity detected
- Every 90 days as standard practice

### How to Rotate

#### 1. Supabase Keys
```bash
# In Supabase Dashboard:
1. Go to Settings → API
2. Click "Reset" next to the key
3. Update .env file with new key
4. Restart application
```

#### 2. JWT Secret
```bash
# Generate new secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env
JWT_SECRET_KEY=new_secret_here

# Restart application (all users will need to re-login)
```

#### 3. Admin Password
```bash
# Update .env with new password
ADMIN_PASSWORD=new_strong_password_here

# Restart application
```

## 🚨 Security Incident Response

### If Credentials Are Exposed

#### Immediate Actions (within 1 hour):
1. **Rotate ALL exposed credentials immediately**
2. **Check Git history** for credential exposure
   ```bash
   git log -p | grep -i "supabase_anon_key\|jwt_secret\|admin_password"
   ```
3. **Remove from Git history** if found
   ```bash
   # This is dangerous - backup first!
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch ai-chat-interface/.env" \
     --prune-empty --tag-name-filter cat -- --all

   # Force push (WARNING: coordinates with team first!)
   git push origin --force --all
   ```

#### Within 24 hours:
4. Review all database logs for suspicious activity
5. Check for unauthorized projects/users
6. Document the incident
7. Update security procedures

### Security Monitoring

#### Regular Checks (Weekly):
- [ ] Review Supabase logs for unusual activity
- [ ] Check for new unauthorized users
- [ ] Verify `.env` is still in `.gitignore`
- [ ] Review failed login attempts

#### Regular Checks (Monthly):
- [ ] Update dependencies (`pip list --outdated`)
- [ ] Review security patches
- [ ] Audit user permissions
- [ ] Test backup/restore procedures

## 📋 Deployment Checklist

### Before Deploying to Production

- [ ] All default passwords changed
- [ ] JWT_SECRET_KEY is strong and random
- [ ] ADMIN_PASSWORD is strong and unique
- [ ] `.env` file is NOT in Git
- [ ] `.gitignore` includes `.env`
- [ ] Supabase RLS policies enabled
- [ ] FLASK_DEBUG=False in production
- [ ] SSL/TLS enabled for all connections
- [ ] Database backups configured
- [ ] Monitoring and logging enabled
- [ ] Security headers configured
- [ ] Rate limiting implemented
- [ ] CORS properly configured

## 🔍 Vulnerability Reporting

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. Email: [your-security-email@example.com]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours.

## 📚 Additional Resources

### Security Tools
- **Password Generator**: https://1password.com/password-generator/
- **Secret Scanner**: https://github.com/trufflesecurity/trufflehog
- **Dependency Scanner**: https://github.com/pyupio/safety

### Best Practices
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Python Security: https://python.readthedocs.io/en/stable/library/security_warnings.html
- Flask Security: https://flask.palletsprojects.com/en/2.3.x/security/

## 🔄 Version History

- **2025-10-11**: Initial security guide created
  - Removed hardcoded credentials from codebase
  - Added environment variable validation
  - Enhanced documentation

---

**Remember**: Security is not a one-time task, it's an ongoing process. Stay vigilant!
