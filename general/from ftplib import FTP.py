from ftplib import FTP

ftp_host = "linux20240907.eastus.cloudapp.azure.com"
ftp_port = 21
ftp_username = "johnny"
ftp_pass = "#a+8%32U48at"

ftp = FTP(ftp_host, user=ftp_username, passwd=ftp_pass)
ftp.set_pasv(0)
ftp.dir()
ftp.cwd("discord/plugins/custom_audio/guild_id")
ftp.dir()
print("Changed dir!")
file = open("C:\\Users\\Ching\\Downloads\\retrieve.htm", "rb")
ftp.storbinary(f'STOR retrieve.htm', file)
# Change permission
print ftp.sendcmd('SITE CHMOD 644 ' + filename)
ftp.close()