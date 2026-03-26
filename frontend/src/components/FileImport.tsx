import { useState, useRef } from 'react';
import { Upload, X, FileText, AlertCircle, Check } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { importApi } from '../api/client';

interface FileImportProps {
  onImport: (items: string[]) => void;
  accept?: string;
  placeholder?: string;
  label?: string;
}

export default function FileImport({
  onImport,
  accept = '.txt,.csv,.xlsx,.xls',
  placeholder = 'Drop file here or click to upload',
  label = 'Import from file',
}: FileImportProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const importMutation = useMutation({
    mutationFn: (file: File) => importApi.importFile(file),
    onSuccess: (result) => {
      onImport(result.items);
      setSelectedFile(null);
    },
  });

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleFile = (file: File) => {
    setSelectedFile(file);
    importMutation.mutate(file);
  };

  const clearFile = () => {
    setSelectedFile(null);
    importMutation.reset();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm text-gray-400">{label}</label>

      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-4 cursor-pointer transition-colors ${
          isDragging
            ? 'border-twitter-blue bg-twitter-blue/10'
            : 'border-[#38444d] hover:border-gray-500'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileSelect}
          className="hidden"
        />

        {selectedFile ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-twitter-blue" />
              <span className="text-white">{selectedFile.name}</span>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                clearFile();
              }}
              className="p-1 hover:bg-[#283340] rounded"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 text-gray-400">
            <Upload className="w-8 h-8" />
            <span className="text-sm">{placeholder}</span>
            <span className="text-xs">Supports .txt, .csv, .xlsx</span>
          </div>
        )}
      </div>

      {/* Status Messages */}
      {importMutation.isPending && (
        <div className="flex items-center gap-2 text-twitter-blue text-sm">
          <div className="w-4 h-4 border-2 border-twitter-blue border-t-transparent rounded-full animate-spin" />
          <span>Importing...</span>
        </div>
      )}

      {importMutation.isSuccess && (
        <div className="flex items-center gap-2 text-green-500 text-sm">
          <Check className="w-4 h-4" />
          <span>Imported {importMutation.data.count} items from {importMutation.data.filename}</span>
        </div>
      )}

      {importMutation.isError && (
        <div className="flex items-center gap-2 text-red-500 text-sm">
          <AlertCircle className="w-4 h-4" />
          <span>
            {importMutation.error instanceof Error
              ? importMutation.error.message
              : 'Import failed'}
          </span>
        </div>
      )}
    </div>
  );
}
