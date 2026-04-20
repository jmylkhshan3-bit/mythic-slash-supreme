import fs from "fs";
import swaggerJsdoc from "swagger-jsdoc";

const options = {
  definition: {
    openapi: "3.0.0",
    info: {
      title: "Kokoro Web API",
      version: "0.0.0",
    },
    components: {
      securitySchemes: {
        bearerAuth: {
          type: "http",
          scheme: "bearer",
          bearerFormat: "JWT",
        },
      },
    },
    security: [
      {
        bearerAuth: [],
      },
    ],
  },
  apis: ["./src/routes/api/**/*.ts"],
};

const openapiSpecification = swaggerJsdoc(options);

if (!fs.existsSync("./static/api/v1")) {
  fs.mkdirSync("./static/api/v1", { recursive: true });
}

fs.writeFileSync(
  "./static/api/v1/openapi.json",
  JSON.stringify(openapiSpecification, null, 2),
);
