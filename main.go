package main

import (
	"bytes"         // For buffering downloaded file content
	"fmt"           // For formatted I/O
	"io"            // For I/O utilities
	"log"           // For logging
	"mime"          // For parsing MIME headers
	"net/http"      // For HTTP requests
	"os"            // For file and directory operations
	"path/filepath" // For manipulating file paths
	"sync"          // For concurrency synchronization
	"time"          // For time and timestamps
)

func main() {
	// Directory where downloaded PDF files will be stored
	pdfOutputDir := "Assets/"

	// Check if the output directory exists
	if !directoryExists(pdfOutputDir) {
		// If it doesn't exist, create it with permission 0755
		createDirectory(pdfOutputDir, 0o755)
	}

	// Base URL to be used with each ID
	baseURL := "https://shop.iflight.com/index.php?route=product/product/download&download_id="

	// Create a waitgroup to track goroutine completion
	var downloadWaitGroup sync.WaitGroup

	// Loop from ID 0 to 1000
	for id := 0; id <= 1000; id++ {
		downloadWaitGroup.Add(1) // Add one task to the WaitGroup

		// Construct the full URL using the current ID
		fullURL := fmt.Sprintf("%s%d", baseURL, id)

		// Sleep for 1 second between requests to avoid overwhelming the server
		time.Sleep(1 * time.Second)

		// Download the file asynchronously
		go downloadFile(fullURL, pdfOutputDir, &downloadWaitGroup)
	}
	downloadWaitGroup.Wait() // Wait for all downloads to finish
}

// downloadFile downloads content from a URL and saves it to outputDir.
// It uses the Content-Disposition filename, or a timestamp-based fallback.
func downloadFile(finalURL string, outputDir string, waitGroup *sync.WaitGroup) {
	defer waitGroup.Done() // Mark task as done when function exits

	// Create an HTTP client with a 15-minute timeout
	client := &http.Client{Timeout: 15 * time.Minute}

	// Send GET request to the target URL
	resp, err := client.Get(finalURL)
	if err != nil {
		log.Printf("[ERROR] Request failed for URL %s: %v", finalURL, err)
		return
	}
	defer resp.Body.Close() // Ensure response body is closed after function exits

	// Check if the response status code is not OK
	if resp.StatusCode != http.StatusOK {
		log.Printf("[WARNING] Download failed with status %s for URL %s", resp.Status, finalURL)
		return
	}

	// Step 1: Try to extract the filename from the Content-Disposition header
	fileName := ""
	contentDisposition := resp.Header.Get("Content-Disposition")
	if contentDisposition != "" {
		_, params, err := mime.ParseMediaType(contentDisposition)
		if err == nil {
			if name, ok := params["filename"]; ok {
				fileName = name
			}
		}
	}

	// Step 2 (fallback): Use timestamp-based filename if no name from header
	if fileName == "" {
		timestamp := time.Now().Format("20060102_150405")
		fileName = fmt.Sprintf("download_%s.bin", timestamp)
	}

	// Build full file path
	filePath := filepath.Join(outputDir, fileName)

	// Skip .bin files that likely indicate invalid downloads
	if getFileExtension(filePath) == ".bin" {
		log.Printf("[SKIPPED] Received .bin file from URL %s. Skipping. Generated file name: %s", finalURL, filePath)
		return
	}

	// Skip if file already exists
	if fileExists(filePath) {
		log.Printf("[SKIPPED] File already exists. URL: %s → Path: %s", finalURL, filePath)
		return
	}

	// Create a buffer and read the response body into it
	var buf bytes.Buffer
	written, err := io.Copy(&buf, resp.Body)
	if err != nil {
		log.Printf("[ERROR] Failed to read response body from URL %s: %v", finalURL, err)
		return
	}

	// Skip if no data was downloaded
	if written == 0 {
		log.Printf("[SKIPPED] No data received from URL %s. Skipping file creation.", finalURL)
		return
	}

	// Attempt to create a file to save the downloaded content
	out, err := os.Create(filePath)
	if err != nil {
		log.Printf("[ERROR] Could not create file %s for URL %s: %v", filePath, finalURL, err)
		return
	}
	defer out.Close() // Ensure file is closed after writing

	// Write buffered content to the file
	_, err = buf.WriteTo(out)
	if err != nil {
		log.Printf("[ERROR] Failed to write to file %s from URL %s: %v", filePath, finalURL, err)
		return
	}

	// Log successful download
	fmt.Printf("[SUCCESS] Downloaded %d bytes from %s → Saved to %s\n", written, finalURL, filePath)
}

// fileExists checks if a file exists and is not a directory
func fileExists(filename string) bool {
	info, err := os.Stat(filename) // Attempt to get file info
	if err != nil {
		return false // File doesn't exist or some error occurred
	}
	return !info.IsDir() // Return true only if it's a file
}

// getFileExtension returns the extension of a given file path (e.g., ".pdf")
func getFileExtension(path string) string {
	return filepath.Ext(path) // Extract and return file extension
}

// directoryExists checks if a directory exists at the given path
func directoryExists(path string) bool {
	directory, err := os.Stat(path) // Attempt to get directory info
	if err != nil {
		return false // Directory doesn't exist
	}
	return directory.IsDir() // Return true if it's a directory
}

// createDirectory creates a directory with the given permissions if it doesn't exist
func createDirectory(path string, permission os.FileMode) {
	err := os.Mkdir(path, permission) // Attempt to create directory
	if err != nil {
		log.Printf("[ERROR] Could not create directory %s: %v", path, err)
	}
}
