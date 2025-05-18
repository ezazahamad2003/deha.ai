import React, { useState } from 'react';
import { 
    Container, 
    Box, 
    Typography, 
    Button, 
    Paper,
    AppBar,
    Toolbar,
    IconButton,
    Drawer,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    useTheme,
    useMediaQuery,
    alpha
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import ChatIcon from '@mui/icons-material/Chat';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import Calendar from './components/Calendar';

function App() {
  const [pdfFile, setPdfFile] = useState(null);
  // pdfText will be used for chat functionality in future updates
  const [pdfText, setPdfText] = useState('');
  const [isCallActive, setIsCallActive] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentView, setCurrentView] = useState('chat');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setPdfFile(file);
      setIsProcessing(true);

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch('http://localhost:5000/upload', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error('Upload failed');
        }

        const data = await response.json();
        setPdfText(data.text);
        setIsProcessing(false);
      } catch (error) {
        console.error('Error uploading PDF:', error);
        setIsProcessing(false);
      }
    } else {
      alert('Please select a valid PDF file');
    }
  };

  const handleStartCall = () => {
    setIsCallActive(true);
  };

  const handleEndCall = () => {
    setIsCallActive(false);
  };

  const toggleDrawer = (open) => (event) => {
    if (event.type === 'keydown' && (event.key === 'Tab' || event.key === 'Shift')) {
      return;
    }
    setDrawerOpen(open);
  };

  const menuItems = [
    { text: 'Chat', icon: <ChatIcon />, view: 'chat' },
    { text: 'Calendar', icon: <CalendarTodayIcon />, view: 'calendar' },
  ];

  const drawer = (
    <Box
      sx={{ 
        width: 250,
        background: 'linear-gradient(180deg, #1976d2 0%, #1565c0 100%)',
        height: '100%',
        color: 'white'
      }}
      role="presentation"
      onClick={toggleDrawer(false)}
      onKeyDown={toggleDrawer(false)}
    >
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
          Deha AI
        </Typography>
      </Box>
      <List>
        {menuItems.map((item) => (
          <ListItem 
            button 
            key={item.text}
            onClick={() => setCurrentView(item.view)}
            selected={currentView === item.view}
            sx={{
              color: 'white',
              '&.Mui-selected': {
                backgroundColor: alpha('#fff', 0.1),
                '&:hover': {
                  backgroundColor: alpha('#fff', 0.15),
                }
              },
              '&:hover': {
                backgroundColor: alpha('#fff', 0.05),
              }
            }}
          >
            <ListItemIcon sx={{ color: 'white' }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%)'
    }}>
      <AppBar 
        position="static" 
        elevation={0}
        sx={{ 
          background: 'linear-gradient(90deg, #1976d2 0%, #1565c0 100%)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={toggleDrawer(true)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            Deha AI
          </Typography>
          {pdfFile && (
            <Button 
              color="inherit" 
              startIcon={<UploadFileIcon />}
              onClick={() => document.getElementById('pdf-upload').click()}
              sx={{
                '&:hover': {
                  backgroundColor: alpha('#fff', 0.1)
                }
              }}
            >
              Change PDF
            </Button>
          )}
        </Toolbar>
      </AppBar>

      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={toggleDrawer(false)}
        PaperProps={{
          sx: {
            backgroundColor: 'transparent',
            boxShadow: 'none'
          }
        }}
      >
        {drawer}
      </Drawer>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4, flex: 1 }}>
        {!pdfFile ? (
          <Paper 
            elevation={3} 
            sx={{ 
              p: 4, 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '60vh',
              background: 'white',
              borderRadius: 2,
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
            }}
          >
            <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold', color: '#1976d2' }}>
              Welcome to Deha AI
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 4, textAlign: 'center' }}>
              Upload your medical record to get started with personalized health insights and reminders
            </Typography>
            <Button
              variant="contained"
              component="label"
              startIcon={<UploadFileIcon />}
              sx={{
                py: 1.5,
                px: 4,
                borderRadius: 2,
                textTransform: 'none',
                fontSize: '1.1rem',
                background: 'linear-gradient(90deg, #1976d2 0%, #1565c0 100%)',
                '&:hover': {
                  background: 'linear-gradient(90deg, #1565c0 0%, #0d47a1 100%)',
                }
              }}
            >
              Upload PDF
              <input
                id="pdf-upload"
                type="file"
                accept=".pdf"
                hidden
                onChange={handleFileChange}
              />
            </Button>
          </Paper>
        ) : (
          <Box>
            {currentView === 'chat' ? (
              <Paper 
                elevation={3} 
                sx={{ 
                  p: 4,
                  background: 'white',
                  borderRadius: 2,
                  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
                }}
              >
                <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                  Medical Record Analysis
                </Typography>
                <Typography variant="body1" paragraph sx={{ color: 'text.secondary', mb: 3 }}>
                  Your medical record has been uploaded. You can now start a voice call to discuss it with our AI assistant.
                </Typography>
                {!isCallActive ? (
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={handleStartCall}
                    disabled={isProcessing}
                    sx={{
                      py: 1.5,
                      px: 4,
                      borderRadius: 2,
                      textTransform: 'none',
                      fontSize: '1.1rem',
                      background: 'linear-gradient(90deg, #1976d2 0%, #1565c0 100%)',
                      '&:hover': {
                        background: 'linear-gradient(90deg, #1565c0 0%, #0d47a1 100%)',
                      }
                    }}
                  >
                    Start Call
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    color="secondary"
                    onClick={handleEndCall}
                    sx={{
                      py: 1.5,
                      px: 4,
                      borderRadius: 2,
                      textTransform: 'none',
                      fontSize: '1.1rem'
                    }}
                  >
                    End Call
                  </Button>
                )}
              </Paper>
            ) : (
              <Calendar />
            )}
          </Box>
        )}
      </Container>
    </Box>
  );
}

export default App; 