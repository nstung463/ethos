FROM node:22-alpine

WORKDIR /app

COPY package.json tsconfig.json tsconfig.app.json vite.config.ts index.html ./
COPY package-lock.json ./
COPY src ./src

RUN npm ci

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
