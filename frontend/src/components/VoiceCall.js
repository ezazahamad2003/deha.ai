import React, { useState, useEffect } from 'react';
import { Button, Box, Typography, Paper, CircularProgress } from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import CallEndIcon from '@mui/icons-material/CallEnd';
import { useTheme } from '@mui/material/styles';

const VoiceCall = () => {
    const [isCallActive, setIsCallActive] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState(null);
    const [transcript, setTranscript] = useState('');
    const [aiResponse, setAiResponse] = useState('');
    const theme = useTheme();

    useEffect(() => {
        // Cleanup function to stop any ongoing audio playback
        return () => {
            setIsCallActive(false);
            setIsProcessing(false);
        };
    }, []);

    const startCall = async () => {
        if (isCallActive) return;
        
        try {
            console.log('Starting call...');
            setError(null);
            setIsCallActive(true);
            setIsProcessing(true);
            
            const response = await fetch('http://localhost:5000/listen', {
                method: 'POST',
                headers: {
                    'Accept': 'audio/mpeg',
                },
            });

            console.log('Response status:', response.status);
            
            if (!response.ok) {
                const errorData = await response.json();
                console.error('Error response:', errorData);
                throw new Error(errorData.error || 'Failed to process audio');
            }

            // Get the audio blob
            const audioBlob = await response.blob();
            console.log('Received audio blob:', audioBlob.size, 'bytes');
            
            if (audioBlob.size === 0) {
                throw new Error('Received empty audio response');
            }

            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);

            // Play the response
            await audio.play();
            console.log('Playing audio response');

            // After audio finishes playing, start listening again if call is still active
            audio.onended = () => {
                console.log('Audio playback finished');
                setIsProcessing(false);
                if (isCallActive) {
                    handleListen();
                }
            };

        } catch (error) {
            console.error('Error during call start:', error);
            setError(error.message);
            setIsProcessing(false);
            setIsCallActive(false);
        }
    };

    const handleListen = async () => {
        if (!isCallActive) return;

        try {
            setIsProcessing(true);
            setError(null);
            console.log('Sending request to /listen endpoint');
            
            const response = await fetch('http://localhost:5000/listen', {
                method: 'POST',
                headers: {
                    'Accept': 'audio/mpeg',
                },
            });

            console.log('Response status:', response.status);
            
            if (!response.ok) {
                const errorData = await response.json();
                console.error('Error response:', errorData);
                throw new Error(errorData.error || 'Failed to process audio');
            }

            // Get the audio blob
            const audioBlob = await response.blob();
            console.log('Received audio blob:', audioBlob.size, 'bytes');
            
            if (audioBlob.size === 0) {
                throw new Error('Received empty audio response');
            }

            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);

            // Play the response
            await audio.play();
            console.log('Playing audio response');

            // After audio finishes playing, start listening again if call is still active
            audio.onended = () => {
                console.log('Audio playback finished');
                setIsProcessing(false);
                if (isCallActive) {
                    handleListen();
                }
            };

        } catch (error) {
            console.error('Error during audio processing:', error);
            setError(error.message);
            setIsProcessing(false);
            if (isCallActive) {
                // Add a small delay before retrying
                setTimeout(() => {
                    handleListen();
                }, 1000);
            }
        }
    };

    const stopCall = () => {
        console.log('Stopping call...');
        setIsCallActive(false);
        setIsProcessing(false);
        setError(null);
        setTranscript('');
        setAiResponse('');
    };

    return (
        <Paper 
            elevation={3} 
            sx={{
                p: 3,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 2,
                maxWidth: 600,
                mx: 'auto',
                mt: 0,
            }}
        >
            <Typography variant="h5" component="h2" gutterBottom>
                Voice Call with Deha AI
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, mb: 2 }} className="voice-call-controls">
                {!isCallActive ? (
                    <Button
                        variant="contained"
                        color="success"
                        startIcon={<MicIcon />}
                        onClick={startCall}
                        className="start-call-btn"
                    >
                        Start Call
                    </Button>
                ) : (
                    <Button
                        variant="contained"
                        color="secondary"
                        startIcon={<CallEndIcon />}
                        onClick={stopCall}
                        disabled={isProcessing}
                        className="end-call-btn"
                    >
                        End Call
                    </Button>
                )}
            </Box>

            {isProcessing && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} className="voice-call-processing">
                    <CircularProgress size={20} />
                    <Typography variant="body1" sx={{ color: 'text.secondary' }}>
                        Processing...
                    </Typography>
                </Box>
            )}

            {isCallActive && !isProcessing && (
                <Typography variant="body1" sx={{ color: '#039be5', fontStyle: 'italic' }}>
                    Listening...
                </Typography>
            )}

            {error && (
                <Typography variant="body2" sx={{ color: 'error.main', mt: 1 }}>
                    {error}
                </Typography>
            )}
        </Paper>
    );
};

export default VoiceCall; 