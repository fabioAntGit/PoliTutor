# Build stage
FROM node:20-slim AS build

WORKDIR /app

# Copy package files from the frontend directory
COPY app/frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend source code
COPY app/frontend/ ./

# Build the application
RUN npm run build

# Production stage
FROM nginx:stable-alpine

# Copy the built files to the nginx html directory
COPY --from=build /app/dist /usr/share/nginx/html

# Add a basic nginx configuration to handle SPA routing if necessary
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
