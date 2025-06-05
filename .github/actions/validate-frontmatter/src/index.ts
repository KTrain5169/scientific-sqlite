import * as fs from 'fs';
import * as path from 'path';
import matter from 'gray-matter';
import Ajv, { ErrorObject } from 'ajv';

// Get input from GitHub Action
const contentDir = process.env.INPUT_CONTENT_DIRECTORY || 'content';

function getAllMarkdownFiles(dir: string): string[] {
  let results: string[] = [];
  const list = fs.readdirSync(dir);
  list.forEach((file) => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat && stat.isDirectory()) {
      results = results.concat(getAllMarkdownFiles(fullPath));
    } else {
      const ext = path.extname(fullPath).toLowerCase();
      if (ext === '.md' || ext === '.mdx') {
        results.push(fullPath);
      }
    }
  });
  return results;
}

function validateFile(filePath: string): void {
  const dir = path.dirname(filePath);
  const schemaPath = path.join(dir, 'schema.json');
  // If no schema found in the same directory, skip validation for this file.
  if (!fs.existsSync(schemaPath)) {
    console.warn(`No schema found in ${dir}. Skipping validation for ${filePath}.`);
    return;
  }
  const schemaContent = fs.readFileSync(schemaPath, 'utf8');
  let schema: any;
  try {
    schema = JSON.parse(schemaContent);
  } catch (error) {
    console.error(`Failed to parse JSON schema at ${schemaPath}: ${error}`);
    process.exit(1);
  }

  const ajv = new Ajv();
  const validate = ajv.compile(schema);
  
  const fileContent = fs.readFileSync(filePath, 'utf8');
  const fm = matter(fileContent);
  const data = fm.data;

  const valid = validate(data);
  if (!valid) {
    console.error(`Schema validation error in file ${filePath}:`);
    (validate.errors as ErrorObject[]).forEach(err => {
      console.error(`  ${err.instancePath} ${err.message}`);
    });
    process.exit(1);
  } else {
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