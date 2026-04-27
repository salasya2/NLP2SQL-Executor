# Stage 1: Build the Vite frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the application
COPY . .

# Build the frontend application (outputs to /app/dist)
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

# Copy the built assets from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the custom Nginx configuration to enable API proxying
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 443 (HTTPS)
EXPOSE 443

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
