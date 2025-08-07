# Use Node.js 18 alpine image as base
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies
RUN npm install

# Copy project files
COPY . .

# Build the Next.js app
RUN npm run build

# Expose port
EXPOSE 3000

# Start the application in development mode for now
CMD ["npm", "run", "dev"]