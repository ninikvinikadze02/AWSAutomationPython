# For MIME types
import magic
mime = magic.Magic(mime=True)
m = mime.from_file("static/test.txt") # 'application/pdf'
print(m.split("/")[-1], m)