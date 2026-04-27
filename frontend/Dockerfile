# Stage 1: Build the Vite frontend
FROM node:18-alpine as builder

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

# Expose port 80 (the default Nginx port)
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
