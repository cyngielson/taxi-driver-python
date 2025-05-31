# Use Kivy's official buildozer image
FROM kivy/buildozer:latest

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Build APK
CMD ["buildozer", "android", "debug"]
