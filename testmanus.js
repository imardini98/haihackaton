require('dotenv').config();
const fs = require('fs');
const https = require('https');
const path = require('path');

// Configuration
const API_KEY = process.env.MANUS_API_KEY;
const POLL_INTERVAL = 30000; // 30 seconds in milliseconds
const OUTPUT_DIR = './csv_files';

// Validate API key
if (!API_KEY) {
  console.error('❌ Error: MANUS_API_KEY not found in .env file');
  console.error('Please create a .env file with: MANUS_API_KEY=your_api_key_here');
  process.exit(1);
}

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Function to create a Manus task
async function createTask(prompt) {
  console.log('Creating Manus task...');
  
  const options = {
    method: 'POST',
    headers: {
      'API_KEY': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      prompt: prompt,
      agentProfile: 'manus-1.6-lite',
      taskMode: 'agent',
      interactiveMode: false
    })
  };

  try {
    const response = await fetch('https://api.manus.ai/v1/tasks', options);
    const data = await response.json();
    
    if (data.task_id) {
      console.log(`✓ Task created successfully!`);
      console.log(`  Task ID: ${data.task_id}`);
      console.log(`  Task URL: ${data.task_url}`);
      return data.task_id;
    } else {
      throw new Error('No task_id returned from API');
    }
  } catch (error) {
    console.error('Error creating task:', error);
    throw error;
  }
}

// Function to get task status
async function getTaskStatus(taskId) {
  const options = {
    method: 'GET',
    headers: {
      'API_KEY': API_KEY
    }
  };

  try {
    const response = await fetch(`https://api.manus.ai/v1/tasks/${taskId}`, options);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting task status:', error);
    throw error;
  }
}

// Function to download file from URL
function downloadFile(url, filepath) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(filepath);
    
    https.get(url, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`Failed to download file: ${response.statusCode}`));
        return;
      }
      
      response.pipe(file);
      
      file.on('finish', () => {
        file.close();
        resolve(filepath);
      });
    }).on('error', (err) => {
      fs.unlink(filepath, () => {}); // Delete incomplete file
      reject(err);
    });
  });
}

// Function to extract and save CSV files from task output
async function extractAndSaveCSVFiles(taskData) {
  console.log('\nExtracting CSV files from task output...');
  
  const csvFiles = [];
  
  // Iterate through output messages
  if (taskData.output && Array.isArray(taskData.output)) {
    for (const message of taskData.output) {
      if (message.content && Array.isArray(message.content)) {
        for (const contentItem of message.content) {
          // Check if this content item has a file URL and is a CSV
          if (contentItem.fileUrl && contentItem.fileName) {
            const fileName = contentItem.fileName.toLowerCase();
            
            if (fileName.endsWith('.csv')) {
              console.log(`  Found CSV: ${contentItem.fileName}`);
              csvFiles.push({
                url: contentItem.fileUrl,
                fileName: contentItem.fileName,
                mimeType: contentItem.mimeType
              });
            }
          }
        }
      }
    }
  }
  
  // Download all CSV files
  if (csvFiles.length > 0) {
    console.log(`\nDownloading ${csvFiles.length} CSV file(s)...`);
    
    for (const csvFile of csvFiles) {
      const outputPath = path.join(OUTPUT_DIR, csvFile.fileName);
      
      try {
        await downloadFile(csvFile.url, outputPath);
        console.log(`  ✓ Saved: ${outputPath}`);
      } catch (error) {
        console.error(`  ✗ Failed to download ${csvFile.fileName}:`, error.message);
      }
    }
    
    console.log(`\n✓ All CSV files processed! Saved to: ${OUTPUT_DIR}`);
  } else {
    console.log('  No CSV files found in task output.');
  }
  
  return csvFiles;
}

// Function to poll task until completion
async function pollTaskUntilComplete(taskId) {
  console.log(`\nPolling task status every ${POLL_INTERVAL / 1000} seconds...`);
  
  let attempts = 0;
  
  while (true) {
    attempts++;
    const taskData = await getTaskStatus(taskId);
    
    const status = taskData.status;
    console.log(`  [${new Date().toLocaleTimeString()}] Attempt ${attempts} - Status: ${status}`);
    
    if (status === 'completed') {
      console.log('\n✓ Task completed successfully!');
      console.log(`  Total credits used: ${taskData.credit_usage || 'N/A'}`);
      return taskData;
    } else if (status === 'failed') {
      console.error('\n✗ Task failed!');
      if (taskData.error) {
        console.error(`  Error: ${taskData.error}`);
      }
      throw new Error('Task failed');
    } else if (status === 'running' || status === 'pending') {
      // Continue polling
      await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));
    } else {
      console.warn(`  Unknown status: ${status}`);
      await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));
    }
  }
}

// Main execution function
async function main() {
  console.log('=== Manus Task System ===\n');
  
  const prompt = 'Role: Senior Research Strategist & Efficiency Engineer Objective: Identify high-value emerging trends for AI technologies and extract "State-of-the-Art" research metadata with zero credit waste. Input Topic: AI technologies Phase 1: Trend Intelligence (Context Filter) Broad Reconnaissance: Execute 3 distinct Google searches focused on the current state of the [Input Topic] (e.g., "latest breakthroughs [topic] [CURRENT_YEAR]", "emerging sub-fields [topic]"). Snippet Analysis: Do not click or read full articles. Analyze only the titles and snippets from the search results to identify the specific technical jargon currently dominating the field. Markdown Synthesis: Create a brief Markdown block titled ## Trend Context listing: The 3 most prevalent technical keywords/sub-fields. 1 "Wildcard" term (a niche but rising concept mentioned in snippets). Phase 2: Tactical Targeting (Dynamic Date) Get Current Date: Identify the current system date. Calculate Lookback: specific strictly the date for exactly 7 days ago from today. Format this date as YYYY-MM-DD. Construct Dorks: Using the specific keywords from Phase 1 and the calculated date, construct 2 surgical Google Dork queries: Format: site:arxiv.org [Phase 1 Keyword] "state-of-the-art" OR "SOTA" after:YYYY-MM-DD Phase 3: Metadata Extraction (Credit Saver Mode) Execution: Run the Dork queries. Scout: Select the top 5 papers based on "Impact Signals" in the snippet (e.g., mentions of benchmarks, "outperforms", or notable labs). Extraction: Extract the following metadata directly from the search snippets or abstract page (Do NOT download/read the PDF). Output Format (CSV Code Block Only): Title, Authors, ArXiv_ID, Direct_PDF_Link (Note: Construct PDF link as https://arxiv.org/pdf/[ID].pdf) ⛔ CRITICAL CREDIT SAVER RULES: Zero-Touch PDF: Never open, render, or summarize the actual PDF files. Domain Lock: After Phase 1, strictly browse arxiv.org. Stop Condition: Once the CSV is generated, stop immediately.';
  
  try {
    // Step 1: Create the task
    const taskId = await createTask(prompt);
    
    // Step 2: Poll until completion
    const completedTask = await pollTaskUntilComplete(taskId);
    
    // Step 3: Extract and save CSV files
    await extractAndSaveCSVFiles(completedTask);
    
    console.log('\n=== Process Complete ===');
  } catch (error) {
    console.error('\n✗ Error in main process:', error.message);
    process.exit(1);
  }
}

// Run the main function
main();


