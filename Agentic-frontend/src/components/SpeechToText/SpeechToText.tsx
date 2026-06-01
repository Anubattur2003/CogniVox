import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FiMic, FiMicOff, FiLoader, FiWifi, FiWifiOff } from 'react-icons/fi';
import { toast } from 'react-hot-toast';

interface SpeechToTextProps {
  onTranscribed: (text: string) => void;
  disabled?: boolean;
  variant?: 'default' | 'compact' | 'modal';
  isDarkMode?: boolean;
  className?: string;
}

export const SpeechToText: React.FC<SpeechToTextProps> = ({
  onTranscribed,
  disabled = false,
  variant = 'default',
  isDarkMode = false,
  className = ''
}) => {
  // Recording states
  const [isRecording, setIsRecording] = useState(false);
  const [audioSupported, setAudioSupported] = useState(false);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
  const [recordingStartTime, setRecordingStartTime] = useState<number | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Recognition method states
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [googleSpeechSupported, setGoogleSpeechSupported] = useState(false);
  const [currentMethod, setCurrentMethod] = useState<'google' | 'local' | null>(null);

  // Refs for audio processing
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingTimeoutRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const silenceTimeoutRef = useRef<number | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  
  // Google Speech Recognition refs
  const googleRecognitionRef = useRef<any>(null);
  const googleTimeoutRef = useRef<number | null>(null);

  // Check support and listen for online/offline events
  useEffect(() => {
    const checkSupport = async () => {
      // Check MediaRecorder support for local fallback
      const hasMediaRecorder = typeof MediaRecorder !== 'undefined';
      const hasGetUserMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
      setAudioSupported(hasMediaRecorder && hasGetUserMedia);
      
      // Check Google Speech Recognition support
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const googleSupported = !!SpeechRecognition;
      setGoogleSpeechSupported(googleSupported);
    };

    const handleOnline = () => {
      setIsOnline(true);
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    checkSupport().catch(console.error);
    
    // Listen for network changes
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      // Cleanup any active streams and audio analysis
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (recordingTimeoutRef.current) {
        clearTimeout(recordingTimeoutRef.current);
      }
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (googleRecognitionRef.current) {
        googleRecognitionRef.current.stop();
      }
      if (googleTimeoutRef.current) {
        clearTimeout(googleTimeoutRef.current);
      }
      
      // Remove network listeners
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Check and request microphone permission before Google Speech Recognition
  const checkMicrophonePermission = async (): Promise<boolean> => {
    try {
      const permission = await navigator.permissions.query({ name: 'microphone' as PermissionName });
      
      if (permission.state === 'granted') {
        return true;
      }
      
      if (permission.state === 'denied') {
        return false;
      }
      
      // If prompt, try to request permission by accessing microphone
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop()); // Clean up
        return true;
      } catch (error) {
        return false;
      }
      
    } catch (error) {
      // Assume we can try - some browsers don't support permissions API
      return true;
    }
  };

  // Google Speech Recognition functions
  const startGoogleRecognition = async () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      return startLocalRecording();
    }

    // Check microphone permission first
    const hasPermission = await checkMicrophonePermission();
    
    if (!hasPermission) {
      return startLocalRecording();
    }

    setCurrentMethod('google');
    setIsRecording(true);

    const recognition = new SpeechRecognition();
    googleRecognitionRef.current = recognition;

    // Configure recognition
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsRecording(true);
    };

    recognition.onresult = (event: any) => {
      const result = event.results[0];
      
      if (result.isFinal) {
        const transcribedText = result[0].transcript.trim();
        
        if (transcribedText && transcribedText.length > 0) {
          onTranscribed(transcribedText);
        }
        
        setIsRecording(false);
        setCurrentMethod(null);
      }
    };

    recognition.onerror = (event: any) => {
      setIsRecording(false);
      setCurrentMethod(null);
      
      // Silent fallback for any error
      setTimeout(() => startLocalRecording(), 100);
    };

    recognition.onend = () => {
      setIsRecording(false);
      setCurrentMethod(null);
    };

    // Auto-stop after 30 seconds as fallback
    googleTimeoutRef.current = setTimeout(() => {
      if (googleRecognitionRef.current) {
        googleRecognitionRef.current.stop();
      }
    }, 30000);

    try {
      recognition.start();
    } catch (error) {
      setIsRecording(false);
      setCurrentMethod(null);
      startLocalRecording();
    }
  };

  const stopGoogleRecognition = () => {
    if (googleRecognitionRef.current) {
      googleRecognitionRef.current.stop();
      googleRecognitionRef.current = null;
    }
    
    if (googleTimeoutRef.current) {
      clearTimeout(googleTimeoutRef.current);
      googleTimeoutRef.current = null;
    }
    
    setIsRecording(false);
    setCurrentMethod(null);
  };

  const startSilenceDetection = async (stream: MediaStream, recordingStarted: number) => {
    // Prevent multiple instances
    if (audioContextRef.current) {
      return;
    }
    
    try {
      // Create audio context and analyser
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const microphone = audioContext.createMediaStreamSource(stream);
      
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.3;
      microphone.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      
      // Resume audio context if needed
      if (audioContext.state === 'suspended') {
        await audioContext.resume();
      }
      
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      let consecutiveSilentFrames = 0;
      const SILENCE_THRESHOLD = 25;
      const SILENCE_DURATION = 1500; // 1.5 seconds of silence
      const MIN_RECORDING_TIME = 800; // Minimum 0.8 seconds
      const FRAMES_PER_SECOND = 60;
      const SILENT_FRAMES_THRESHOLD = Math.floor((SILENCE_DURATION / 1000) * FRAMES_PER_SECOND);
      
      const checkAudioLevel = () => {
        // First check if everything is still valid
        if (!analyserRef.current || !mediaRecorderRef.current || mediaRecorderRef.current.state !== 'recording') {
          return;
        }
        
        try {
          analyser.getByteFrequencyData(dataArray);
          
          // Calculate RMS (Root Mean Square) for better volume detection
          let sum = 0;
          for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i] * dataArray[i];
          }
          const rms = Math.sqrt(sum / bufferLength);
          
          const now = Date.now();
          const recordingDuration = now - recordingStarted;
          
          // Only start silence detection after minimum recording time
          if (recordingDuration < MIN_RECORDING_TIME) {
            consecutiveSilentFrames = 0;
            animationFrameRef.current = requestAnimationFrame(checkAudioLevel);
            return;
          }
          
          if (rms < SILENCE_THRESHOLD) {
            consecutiveSilentFrames++;
            
            // Check if we've been silent long enough
            if (consecutiveSilentFrames >= SILENT_FRAMES_THRESHOLD) {
              // Direct MediaRecorder stop to avoid race condition
              if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
                mediaRecorderRef.current.stop();
                
                // Clean up silence detection immediately
                setIsRecording(false);
                setCurrentMethod(null);
                if (recordingTimeoutRef.current) {
                  clearTimeout(recordingTimeoutRef.current);
                  recordingTimeoutRef.current = null;
                }
                if (animationFrameRef.current) {
                  cancelAnimationFrame(animationFrameRef.current);
                  animationFrameRef.current = null;
                }
                if (audioContextRef.current) {
                  audioContextRef.current.close();
                  audioContextRef.current = null;
                }
              }
              return;
            }
          } else {
            consecutiveSilentFrames = 0;
          }
          
          // Continue monitoring
          animationFrameRef.current = requestAnimationFrame(checkAudioLevel);
          
        } catch (error) {
          animationFrameRef.current = requestAnimationFrame(checkAudioLevel);
        }
      };
      
      // Start monitoring
      checkAudioLevel();
      
    } catch (error) {
      // Fallback to manual/timeout-only stopping
    }
  };

  const stopLocalRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Clear all timeouts and cleanup audio analysis
      if (recordingTimeoutRef.current) {
        clearTimeout(recordingTimeoutRef.current);
        recordingTimeoutRef.current = null;
      }
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
        silenceTimeoutRef.current = null;
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
    }
  };

  const transcribeAudioLocally = async (audioBlob: Blob) => {
    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'audio.wav');
      
      // Call the local transcription API
      const response = await fetch('http://localhost:8002/api/transcribe', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Server error (${response.status})`);
      }
      
      const transcriptionData = await response.json();
      
      if (transcriptionData.success && transcriptionData.text) {
        // Clean up the transcribed text
        const transcribedText = transcriptionData.text.trim();
        
        // Only add non-placeholder text
        if (transcribedText && 
            !transcribedText.includes('🎤 Audio recorded') && 
            !transcribedText.includes('Setup needed') &&
            transcribedText.length > 2) {
          onTranscribed(transcribedText);
        }
      }
      
    } catch (error) {
      // Only show critical errors that user needs to know about
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      if (errorMessage.includes('Failed to fetch') || errorMessage.includes('network')) {
        toast.error('Local speech service unavailable. Please ensure the backend is running.');
      } else if (errorMessage.includes('Server error')) {
        toast.error('Local speech service error. Please try again.');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const startLocalRecording = async () => {
    setCurrentMethod('local');
    
    if (!audioSupported) {
      toast.error('Audio recording is not supported in this browser.');
      return;
    }

    if (isRecording) {
      stopLocalRecording();
      return;
    }

    if (isProcessing) {
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      const chunks: Blob[] = [];
      const startTime = Date.now();
      setRecordingStartTime(startTime);
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const recordingDuration = Date.now() - startTime;
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        setAudioChunks([audioBlob]);
        
        // Check if recording is too short (less than 0.5 seconds) or empty
        if (recordingDuration < 500 || audioBlob.size < 1000) {
          // Silent cleanup without notification
          setIsRecording(false);
          setIsProcessing(false);
          setRecordingStartTime(null);
          setCurrentMethod(null);
          stream.getTracks().forEach(track => track.stop());
          streamRef.current = null;
          return;
        }
        
        // Process the audio using local speech-to-text agent
        setIsProcessing(true);
        await transcribeAudioLocally(audioBlob);
        
        // Cleanup
        stream.getTracks().forEach(track => track.stop());
        streamRef.current = null;
        setRecordingStartTime(null);
        setCurrentMethod(null);
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      
      // Start silence detection with start time
      await startSilenceDetection(stream, startTime);
      
      // Auto-stop after 30 seconds as fallback
      recordingTimeoutRef.current = setTimeout(() => {
        if (isRecording && mediaRecorderRef.current) {
          stopLocalRecording();
        }
      }, 30000);
      
    } catch (error) {
      setIsRecording(false);
      setIsProcessing(false);
      setRecordingStartTime(null);
      setCurrentMethod(null);
      
      if (error instanceof DOMException && error.name === 'NotAllowedError') {
        toast.error('Microphone access denied. Please allow microphone access.');
      } else if (error instanceof DOMException && error.name === 'NotFoundError') {
        toast.error('No microphone found. Please check your device.');
      } else {
        toast.error('Failed to start recording. Please try again.');
      }
    }
  };

  // Main speech recognition functions that choose the best method
  const startRecording = async () => {
    if (disabled) {
      return;
    }

    if (isRecording) {
      stopRecording();
      return;
    }

    if (isProcessing) {
      return;
    }

    // Determine which method to use based on availability and online status
    const canUseGoogle = isOnline && googleSpeechSupported;
    const canUseLocal = audioSupported;
    
    if (canUseGoogle) {
      await startGoogleRecognition();
    } else if (canUseLocal) {
      startLocalRecording();
    } else {
      toast.error('Speech recognition not available in this browser.');
    }
  };

  const stopRecording = () => {
    if (currentMethod === 'google') {
      stopGoogleRecognition();
    } else if (currentMethod === 'local') {
      stopLocalRecording();
    } else {
      // Fallback - stop any active recording
      if (googleRecognitionRef.current) {
        stopGoogleRecognition();
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        stopLocalRecording();
      }
    }
  };

  return (
    <motion.button
      type="button"
      whileHover={{ scale: (googleSpeechSupported || audioSupported) && !disabled && !isProcessing ? 1.05 : 1 }}
      whileTap={{ scale: (googleSpeechSupported || audioSupported) && !disabled && !isProcessing ? 0.95 : 1 }}
      onClick={isRecording ? stopRecording : startRecording}
      disabled={disabled || (!googleSpeechSupported && !audioSupported) || isProcessing}
      className={`flex items-center justify-center w-7 h-7 rounded-md transition-all duration-200 ${
        (!googleSpeechSupported && !audioSupported)
          ? isDarkMode
            ? 'text-gray-600 cursor-not-allowed opacity-50'
            : 'text-gray-400 cursor-not-allowed opacity-50'
          : isProcessing
            ? isDarkMode
              ? 'bg-blue-600 text-white cursor-not-allowed'
              : 'bg-blue-500 text-white cursor-not-allowed'
          : isRecording
            ? currentMethod === 'google'
              ? isDarkMode
                ? 'bg-green-600 hover:bg-green-700 text-white shadow-lg'
                : 'bg-green-500 hover:bg-green-600 text-white shadow-lg'
              : isDarkMode
                ? 'bg-red-600 hover:bg-red-700 text-white shadow-lg'
                : 'bg-red-500 hover:bg-red-600 text-white shadow-lg'
            : isDarkMode
              ? 'text-gray-400 hover:text-gray-300 hover:bg-gray-700'
              : 'text-gray-500 hover:text-gray-600 hover:bg-gray-100'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
      title={
        (!googleSpeechSupported && !audioSupported)
          ? "Speech recognition not supported in this browser"
          : isProcessing
            ? currentMethod === 'google'
              ? "Processing with Google Speech Recognition..."
              : "Processing with local speech recognition..."
          : isRecording 
            ? currentMethod === 'google'
              ? "Google Speech Recognition active - click to stop"
              : "Local recording active - auto-stops on silence or click to stop"
            : isOnline && googleSpeechSupported
              ? "Click to start voice recording (Google Speech Recognition)"
              : audioSupported
                ? "Click to start voice recording (local speech-to-text)"
                : "Speech recognition not available"
      }
    >
      <motion.div
        animate={
          isRecording 
            ? currentMethod === 'google'
              ? { scale: [1, 1.2, 1] } 
              : { scale: [1, 1.3, 1] }
            : isProcessing 
              ? { rotate: 360 }
              : {}
        }
        transition={
          isRecording 
            ? currentMethod === 'google'
              ? { duration: 1.2, repeat: Infinity, ease: "easeInOut" }
              : { duration: 0.8, repeat: Infinity, ease: "easeInOut" }
            : isProcessing 
              ? { duration: 1, repeat: Infinity, ease: "linear" }
              : {}
        }
        className="relative"
      >
        {isProcessing ? (
          <FiLoader className="w-3.5 h-3.5" />
        ) : isRecording ? (
          currentMethod === 'google' ? (
            <FiMic className="w-3.5 h-3.5" />
          ) : (
            <FiMicOff className="w-3.5 h-3.5" />
          )
        ) : (
          <FiMic className="w-3.5 h-3.5" />
        )}
        
        {/* Small indicator for recognition method */}
        {!isProcessing && (
          <div className="absolute -bottom-0.5 -right-0.5">
            {isOnline && googleSpeechSupported ? (
              <FiWifi className="w-1.5 h-1.5 text-green-500" />
            ) : audioSupported ? (
              <FiWifiOff className="w-1.5 h-1.5 text-orange-500" />
            ) : null}
          </div>
        )}
      </motion.div>
    </motion.button>
  );
};

export default SpeechToText; 