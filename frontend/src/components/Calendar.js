import React, { useState, useEffect } from 'react';
import { 
    Box, 
    Typography, 
    Paper, 
    List, 
    ListItem, 
    ListItemText, 
    Chip,
    Grid,
    Divider,
    CircularProgress
} from '@mui/material';

const Calendar = () => {
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchEvents();
    }, []);

    const fetchEvents = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('http://localhost:5000/extract-events', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch events');
            }
            
            const data = await response.json();
            setEvents(data.events || []);
        } catch (err) {
            setError(err.message);
            console.error('Error fetching events:', err);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    const getPriorityColor = (priority) => {
        switch (priority.toLowerCase()) {
            case 'high':
                return 'error';
            case 'medium':
                return 'warning';
            case 'low':
                return 'success';
            default:
                return 'default';
        }
    };

    const getTypeColor = (type) => {
        switch (type.toLowerCase()) {
            case 'appointment':
                return 'primary';
            case 'medication':
                return 'secondary';
            case 'test':
                return 'info';
            case 'followup':
                return 'success';
            case 'reminder':
                return 'warning';
            default:
                return 'default';
        }
    };

    if (loading) {
        return (
            <Box sx={{ 
                p: 3, 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center',
                minHeight: '400px'
            }}>
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Box sx={{ 
                p: 3, 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center',
                minHeight: '400px'
            }}>
                <Typography color="error" variant="h6">Error: {error}</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Typography 
                variant="h4" 
                gutterBottom 
                sx={{ 
                    fontWeight: 'bold', 
                    color: '#1976d2',
                    mb: 4
                }}
            >
                Medical Calendar & Reminders
            </Typography>
            
            <Grid container spacing={3}>
                {/* Upcoming Events */}
                <Grid item xs={12} md={6}>
                    <Paper 
                        elevation={3} 
                        sx={{ 
                            p: 3, 
                            height: '100%',
                            background: 'white',
                            borderRadius: 2,
                            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
                        }}
                    >
                        <Typography 
                            variant="h6" 
                            gutterBottom 
                            sx={{ 
                                fontWeight: 'bold',
                                color: '#1976d2',
                                mb: 2
                            }}
                        >
                            Upcoming Events
                        </Typography>
                        <List>
                            {events
                                .filter(event => new Date(event.date) >= new Date())
                                .sort((a, b) => new Date(a.date) - new Date(b.date))
                                .map((event, index) => (
                                    <React.Fragment key={index}>
                                        <ListItem sx={{ py: 2 }}>
                                            <ListItemText
                                                primary={
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                                                        <Typography 
                                                            variant="subtitle1" 
                                                            sx={{ 
                                                                fontWeight: 'medium',
                                                                color: '#1976d2'
                                                            }}
                                                        >
                                                            {formatDate(event.date)}
                                                            {event.time && ` at ${event.time}`}
                                                        </Typography>
                                                        <Chip 
                                                            label={event.type} 
                                                            size="small" 
                                                            color={getTypeColor(event.type)}
                                                            sx={{ 
                                                                fontWeight: 'medium',
                                                                borderRadius: 1
                                                            }}
                                                        />
                                                        <Chip 
                                                            label={event.priority} 
                                                            size="small" 
                                                            color={getPriorityColor(event.priority)}
                                                            sx={{ 
                                                                fontWeight: 'medium',
                                                                borderRadius: 1
                                                            }}
                                                        />
                                                    </Box>
                                                }
                                                secondary={
                                                    <Typography 
                                                        variant="body2" 
                                                        sx={{ 
                                                            mt: 1,
                                                            color: 'text.secondary'
                                                        }}
                                                    >
                                                        {event.description}
                                                    </Typography>
                                                }
                                            />
                                        </ListItem>
                                        {index < events.length - 1 && <Divider />}
                                    </React.Fragment>
                                ))}
                        </List>
                    </Paper>
                </Grid>

                {/* Reminders */}
                <Grid item xs={12} md={6}>
                    <Paper 
                        elevation={3} 
                        sx={{ 
                            p: 3, 
                            height: '100%',
                            background: 'white',
                            borderRadius: 2,
                            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
                        }}
                    >
                        <Typography 
                            variant="h6" 
                            gutterBottom 
                            sx={{ 
                                fontWeight: 'bold',
                                color: '#1976d2',
                                mb: 2
                            }}
                        >
                            Reminders
                        </Typography>
                        <List>
                            {events
                                .filter(event => event.type === 'reminder' || event.type === 'medication')
                                .map((event, index) => (
                                    <React.Fragment key={index}>
                                        <ListItem sx={{ py: 2 }}>
                                            <ListItemText
                                                primary={
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                                                        <Typography 
                                                            variant="subtitle1"
                                                            sx={{ 
                                                                fontWeight: 'medium',
                                                                color: '#1976d2'
                                                            }}
                                                        >
                                                            {event.description}
                                                        </Typography>
                                                        {event.recurring && (
                                                            <Chip 
                                                                label="Recurring" 
                                                                size="small" 
                                                                color="info"
                                                                sx={{ 
                                                                    fontWeight: 'medium',
                                                                    borderRadius: 1
                                                                }}
                                                            />
                                                        )}
                                                    </Box>
                                                }
                                                secondary={
                                                    <Typography 
                                                        variant="body2" 
                                                        sx={{ 
                                                            mt: 1,
                                                            color: 'text.secondary'
                                                        }}
                                                    >
                                                        {event.time 
                                                            ? `Daily at ${event.time}`
                                                            : 'Daily reminder'}
                                                    </Typography>
                                                }
                                            />
                                        </ListItem>
                                        {index < events.length - 1 && <Divider />}
                                    </React.Fragment>
                                ))}
                        </List>
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default Calendar;