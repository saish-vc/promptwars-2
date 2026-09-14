FROM node:22-alpine

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .

RUN npm run build

ENV NODE_ENV=production
EXPOSE 8000

CMD ["npx", "--yes", "serve", "dist", "--listen", "8000", "--single"]
