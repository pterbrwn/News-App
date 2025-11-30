import config
print(f"Email: {config.SMTP_EMAIL}")
print(f"Password Length: {len(str(config.SMTP_PASSWORD))}") 
# We check length, don't print the actual password!
