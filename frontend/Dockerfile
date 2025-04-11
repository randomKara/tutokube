# frontend/Dockerfile

# Use the official Nginx image
FROM nginx:stable-alpine

# Copy the static website content to the default Nginx public directory
COPY index.html /usr/share/nginx/html/index.html

# Copy the custom Nginx configuration file
# This overwrites the default configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# The default Nginx command starts the server
# CMD ["nginx", "-g", "daemon off;"] is inherited from the base image