"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const gray_matter_1 = __importDefault(require("gray-matter"));
const ajv_1 = __importDefault(require("ajv"));
// Get input from GitHub Action
const contentDir = process.env.INPUT_CONTENT_DIRECTORY || 'content';
function getAllMarkdownFiles(dir) {
    let results = [];
    const list = fs.readdirSync(dir);
    list.forEach((file) => {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);
        if (stat && stat.isDirectory()) {
            results = results.concat(getAllMarkdownFiles(fullPath));
        }
        else {
            const ext = path.extname(fullPath).toLowerCase();
            if (ext === '.md' || ext === '.mdx') {
                results.push(fullPath);
            }
        }
    });
    return results;
}
function validateFile(filePath) {
    const dir = path.dirname(filePath);
    const schemaPath = path.join(dir, 'schema.json');
    // If no schema found in the same directory, skip validation for this file.
    if (!fs.existsSync(schemaPath)) {
        console.warn(`No schema found in ${dir}. Skipping validation for ${filePath}.`);
        return;
    }
    const schemaContent = fs.readFileSync(schemaPath, 'utf8');
    let schema;
    try {
        schema = JSON.parse(schemaContent);
    }
    catch (error) {
        console.error(`Failed to parse JSON schema at ${schemaPath}: ${error}`);
        process.exit(1);
    }
    const ajv = new ajv_1.default();
    const validate = ajv.compile(schema);
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const fm = (0, gray_matter_1.default)(fileContent);
    const data = fm.data;
    const valid = validate(data);
    if (!valid) {
        console.error(`Schema validation error in file ${filePath}:`);
        validate.errors.forEach(err => {
            console.error(`  ${err.instancePath} ${err.message}`);
        });
        process.exit(1);
    }
    else {
        console.log(`Validation passed for file ${filePath}`);
    }
}
function runValidation() {
    console.log(`Scanning content in: ${contentDir}`);
    if (!fs.existsSync(contentDir)) {
        console.error(`Content directory ${contentDir} does not exist.`);
        process.exit(1);
    }
    const files = getAllMarkdownFiles(contentDir);
    if (!files.length) {
        console.log(`No Markdown files found in ${contentDir}.`);
        return;
    }
    files.forEach(validateFile);
    console.log('All files validated successfully.');
}
runValidation();
