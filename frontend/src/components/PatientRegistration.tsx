// Patient Registration Component for Smart Triage Kiosk
// Multilingual, accessible patient intake form with voice guidance

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  RadioGroup,
  Radio,
  FormLabel,
  Chip,
  Alert,
  AlertTitle,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Autocomplete,
  CircularProgress,
  Tooltip,
  Fab,
  Switch,
  Divider,
  LinearProgress
} from '@mui/material';
import {
  Person as PersonIcon,
  ContactPhone as ContactIcon,
  MedicalServices as MedicalIcon,
  VolumeUp as SpeakIcon,
  VolumeOff as MuteIcon,
  Accessibility as AccessibilityIcon,
  Language as LanguageIcon,
  PhotoCamera as CameraIcon,
  QrCodeScanner as QrIcon,
  Save as SaveIcon,
  Clear as ClearIcon,
  ArrowBack as BackIcon,
  ArrowForward as NextIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Check as CheckIcon,
  Edit as EditIcon,
  PersonAdd as NewPatientIcon,
  Search as SearchIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon,
  Translate as TranslateIcon
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { format } from 'date-fns';

// Internationalization
const translations = {
  en: {
    title: 'Patient Registration',
    welcome: 'Welcome to Smart Triage',
    instruction: 'Please provide your information to begin the triage process',
    demographics: 'Personal Information',
    contact: 'Contact Details',
    medical: 'Medical Information',
    emergency: 'Emergency Contact',
    consent: 'Consent & Privacy',
    firstName: 'First Name',
    lastName: 'Last Name',
    dateOfBirth: 'Date of Birth',
    gender: 'Gender',
    phoneNumber: 'Phone Number',
    email: 'Email Address',
    address: 'Address',
    emergencyContact: 'Emergency Contact Name',
    emergencyPhone: 'Emergency Contact Phone',
    relationship: 'Relationship',
    allergies: 'Known Allergies',
    medications: 'Current Medications',
    conditions: 'Medical Conditions',
    insurance: 'Insurance Information',
    consentTreatment: 'I consent to treatment',
    consentData: 'I consent to data processing',
    next: 'Next',
    back: 'Back',
    save: 'Save Registration',
    clear: 'Clear Form',
    required: 'Required field',
    optional: 'Optional',
    search: 'Search existing patient',
    newPatient: 'New Patient',
    voiceGuidance: 'Voice Guidance',
    accessibility: 'Accessibility Options'
  },
  hi: {
    title: 'रोगी पंजीकरण',
    welcome: 'स्मार्ट ट्राइएज में आपका स्वागत है',
    instruction: 'कृपया ट्राइएज प्रक्रिया शुरू करने के लिए अपनी जानकारी प्रदान करें',
    demographics: 'व्यक्तिगत जानकारी',
    contact: 'संपर्क विवरण',
    medical: 'चिकित्सा जानकारी',
    emergency: 'आपातकालीन संपर्क',
    consent: 'सहमति और गोपनीयता',
    firstName: 'पहला नाम',
    lastName: 'अंतिम नाम',
    dateOfBirth: 'जन्म की तारीख',
    gender: 'लिंग',
    phoneNumber: 'फोन नंबर',
    email: 'ईमेल पता',
    address: 'पता',
    emergencyContact: 'आपातकालीन संपर्क नाम',
    emergencyPhone: 'आपातकालीन संपर्क फोन',
    relationship: 'रिश्ता',
    allergies: 'ज्ञात एलर्जी',
    medications: 'वर्तमान दवाएं',
    conditions: 'चिकित्सा स्थितियां',
    insurance: 'बीमा जानकारी',
    consentTreatment: 'मैं उपचार के लिए सहमत हूं',
    consentData: 'मैं डेटा प्रोसेसिंग के लिए सहमत हूं',
    next: 'अगला',
    back: 'वापस',
    save: 'पंजीकरण सहेजें',
    clear: 'फॉर्म साफ करें',
    required: 'आवश्यक क्षेत्र',
    optional: 'वैकल्पिक',
    search: 'मौजूदा रोगी खोजें',
    newPatient: 'नया रोगी',
    voiceGuidance: 'आवाज मार्गदर्शन',
    accessibility: 'पहुंच विकल्प'
  }
  // Add more languages as needed
};

// Type definitions
interface PatientData {
  // Demographics
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  gender: string;
  phoneNumber: string;
  email?: string;
  address?: string;
  
  // Emergency Contact
  emergencyContactName?: string;
  emergencyContactPhone?: string;
  emergencyContactRelationship?: string;
  
  // Medical Information
  allergies: string[];
  currentMedications: string[];
  medicalConditions: string[];
  insuranceInfo?: string;
  
  // Consent
  consentTreatment: boolean;
  consentDataProcessing: boolean;
  
  // System fields
  preferredLanguage: string;
  accessibilityNeeds: string[];
}

interface AccessibilitySettings {
  voiceGuidance: boolean;
  largeText: boolean;
  highContrast: boolean;
  screenReader: boolean;
  voiceInput: boolean;
}

// Voice synthesis utility
class VoiceGuidance {
  private synthesis: SpeechSynthesis;
  private enabled: boolean = false;
  private language: string = 'en-US';

  constructor() {
    this.synthesis = window.speechSynthesis;
  }

  setEnabled(enabled: boolean) {
    this.enabled = enabled;
  }

  setLanguage(language: string) {
    this.language = language === 'hi' ? 'hi-IN' : 'en-US';
  }

  speak(text: string) {
    if (!this.enabled || !this.synthesis) return;

    // Cancel any ongoing speech
    this.synthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = this.language;
    utterance.rate = 0.9;
    utterance.volume = 0.8;

    this.synthesis.speak(utterance);
  }

  stop() {
    if (this.synthesis) {
      this.synthesis.cancel();
    }
  }
}

// Patient Registration Form Component
export const PatientRegistrationForm: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [language, setLanguage] = useState('en');
  const [patientData, setPatientData] = useState<PatientData>({
    firstName: '',
    lastName: '',
    dateOfBirth: '',
    gender: '',
    phoneNumber: '',
    email: '',
    address: '',
    emergencyContactName: '',
    emergencyContactPhone: '',
    emergencyContactRelationship: '',
    allergies: [],
    currentMedications: [],
    medicalConditions: [],
    insuranceInfo: '',
    consentTreatment: false,
    consentDataProcessing: false,
    preferredLanguage: 'en',
    accessibilityNeeds: []
  });
  
  const [accessibility, setAccessibility] = useState<AccessibilitySettings>({
    voiceGuidance: false,
    largeText: false,
    highContrast: false,
    screenReader: false,
    voiceInput: false
  });
  
  const [voiceGuidance] = useState(() => new VoiceGuidance());
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  
  const theme = useTheme();
  const t = translations[language as keyof typeof translations] || translations.en;

  // Initialize voice guidance
  useEffect(() => {
    voiceGuidance.setEnabled(accessibility.voiceGuidance);
    voiceGuidance.setLanguage(language);
  }, [accessibility.voiceGuidance, language, voiceGuidance]);

  // Speak step introduction when step changes
  useEffect(() => {
    if (accessibility.voiceGuidance) {
      const stepTexts = [
        t.demographics,
        t.contact,
        t.medical,
        t.emergency,
        t.consent
      ];
      if (stepTexts[activeStep]) {
        setTimeout(() => voiceGuidance.speak(stepTexts[activeStep]), 500);
      }
    }
  }, [activeStep, accessibility.voiceGuidance, t, voiceGuidance]);

  // Form validation
  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};

    switch (step) {
      case 0: // Demographics
        if (!patientData.firstName) newErrors.firstName = t.required;
        if (!patientData.lastName) newErrors.lastName = t.required;
        if (!patientData.dateOfBirth) newErrors.dateOfBirth = t.required;
        if (!patientData.gender) newErrors.gender = t.required;
        break;
      
      case 1: // Contact
        if (!patientData.phoneNumber) newErrors.phoneNumber = t.required;
        if (patientData.email && !/\S+@\S+\.\S+/.test(patientData.email)) {
          newErrors.email = 'Invalid email format';
        }
        break;
      
      case 4: // Consent
        if (!patientData.consentTreatment) newErrors.consentTreatment = t.required;
        if (!patientData.consentDataProcessing) newErrors.consentDataProcessing = t.required;
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const handleFieldChange = (field: keyof PatientData, value: any) => {
    setPatientData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
    
    // Provide voice feedback for important fields
    if (accessibility.voiceGuidance && ['firstName', 'lastName', 'phoneNumber'].includes(field)) {
      voiceGuidance.speak(`${field} updated`);
    }
  };

  const handleArrayFieldAdd = (field: keyof PatientData, value: string) => {
    if (!value.trim()) return;
    
    const currentArray = patientData[field] as string[] || [];
    if (!currentArray.includes(value.trim())) {
      handleFieldChange(field, [...currentArray, value.trim()]);
    }
  };

  const handleArrayFieldRemove = (field: keyof PatientData, value: string) => {
    const currentArray = patientData[field] as string[] || [];
    handleFieldChange(field, currentArray.filter(item => item !== value));
  };

  const savePatientRegistration = async () => {
    if (!validateStep(activeStep)) return;

    setSaving(true);
    try {
      const response = await fetch('/api/v1/patients/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          first_name: patientData.firstName,
          last_name: patientData.lastName,
          date_of_birth: patientData.dateOfBirth,
          gender: patientData.gender,
          phone_number: patientData.phoneNumber,
          email: patientData.email,
          address: patientData.address,
          emergency_contact_name: patientData.emergencyContactName,
          emergency_contact_phone: patientData.emergencyContactPhone,
          emergency_contact_relationship: patientData.emergencyContactRelationship,
          known_allergies: patientData.allergies,
          current_medications: patientData.currentMedications,
          medical_conditions: patientData.medicalConditions,
          insurance_info: patientData.insuranceInfo,
          preferred_language: language,
          accessibility_needs: accessibility
        })
      });

      if (!response.ok) {
        throw new Error('Registration failed');
      }

      const result = await response.json();
      console.log('Patient registered:', result);
      
      if (accessibility.voiceGuidance) {
        voiceGuidance.speak('Registration completed successfully');
      }

      // Navigate to triage assessment
      // This would typically use a router
      window.location.href = `/triage/${result.id}`;
      
    } catch (error) {
      console.error('Registration error:', error);
      if (accessibility.voiceGuidance) {
        voiceGuidance.speak('Registration failed. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  // Search existing patients
  const searchPatients = async (query: string) => {
    if (query.length < 3) return;
    
    setSearching(true);
    try {
      const response = await fetch(`/api/v1/patients/search?q=${encodeURIComponent(query)}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const results = await response.json();
        setSearchResults(results.patients || []);
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setSearching(false);
    }
  };

  const steps = [
    {
      label: t.demographics,
      content: (
        <DemographicsStep
          data={patientData}
          onChange={handleFieldChange}
          errors={errors}
          t={t}
          accessibility={accessibility}
          voiceGuidance={voiceGuidance}
        />
      )
    },
    {
      label: t.contact,
      content: (
        <ContactStep
          data={patientData}
          onChange={handleFieldChange}
          errors={errors}
          t={t}
          accessibility={accessibility}
        />
      )
    },
    {
      label: t.medical,
      content: (
        <MedicalHistoryStep
          data={patientData}
          onArrayAdd={handleArrayFieldAdd}
          onArrayRemove={handleArrayFieldRemove}
          onChange={handleFieldChange}
          t={t}
          accessibility={accessibility}
        />
      )
    },
    {
      label: t.emergency,
      content: (
        <EmergencyContactStep
          data={patientData}
          onChange={handleFieldChange}
          errors={errors}
          t={t}
          accessibility={accessibility}
        />
      )
    },
    {
      label: t.consent,
      content: (
        <ConsentStep
          data={patientData}
          onChange={handleFieldChange}
          errors={errors}
          t={t}
          accessibility={accessibility}
        />
      )
    }
  ];

  return (
    <Box sx={{ 
      maxWidth: 800, 
      mx: 'auto', 
      p: 3,
      fontSize: accessibility.largeText ? '1.2rem' : 'inherit'
    }}>
      {/* Header */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <PersonIcon color="primary" sx={{ fontSize: 32 }} />
            <Box>
              <Typography variant="h4" component="h1">
                {t.title}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {t.instruction}
              </Typography>
            </Box>
          </Box>
          
          {/* Language and Accessibility Controls */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Language</InputLabel>
              <Select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                label="Language"
              >
                <MenuItem value="en">English</MenuItem>
                <MenuItem value="hi">हिंदी</MenuItem>
              </Select>
            </FormControl>
            
            <AccessibilityControls
              settings={accessibility}
              onChange={setAccessibility}
              t={t}
            />
          </Box>
        </Box>
      </Paper>

      {/* Patient Search */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {t.search}
          </Typography>
          <TextField
            fullWidth
            placeholder="Search by name, phone number, or patient ID..."
            onChange={(e) => searchPatients(e.target.value)}
            InputProps={{
              endAdornment: searching ? <CircularProgress size={20} /> : <SearchIcon />
            }}
          />
          {searchResults.length > 0 && (
            <List>
              {searchResults.map((patient: any) => (
                <ListItem key={patient.id} button>
                  <ListItemText
                    primary={`${patient.first_name} ${patient.last_name}`}
                    secondary={`DOB: ${patient.date_of_birth} • Phone: ${patient.phone_number}`}
                  />
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Registration Steps */}
      <Card>
        <CardContent>
          <Stepper activeStep={activeStep} orientation="vertical">
            {steps.map((step, index) => (
              <Step key={index}>
                <StepLabel>{step.label}</StepLabel>
                <StepContent>
                  <Box sx={{ mt: 2, mb: 2 }}>
                    {step.content}
                  </Box>
                  
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                      disabled={index === 0}
                      onClick={handleBack}
                      startIcon={<BackIcon />}
                    >
                      {t.back}
                    </Button>
                    
                    {index === steps.length - 1 ? (
                      <Button
                        variant="contained"
                        onClick={savePatientRegistration}
                        disabled={saving}
                        startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
                      >
                        {saving ? 'Saving...' : t.save}
                      </Button>
                    ) : (
                      <Button
                        variant="contained"
                        onClick={handleNext}
                        endIcon={<NextIcon />}
                      >
                        {t.next}
                      </Button>
                    )}
                  </Box>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>

      {/* Voice Control FAB */}
      {accessibility.voiceGuidance && (
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          onClick={() => voiceGuidance.speak(steps[activeStep]?.label || '')}
        >
          <SpeakIcon />
        </Fab>
      )}
    </Box>
  );
};

// Individual Step Components
const DemographicsStep: React.FC<any> = ({ data, onChange, errors, t, accessibility, voiceGuidance }) => (
  <Grid container spacing={2}>
    <Grid item xs={12} sm={6}>
      <TextField
        fullWidth
        required
        label={t.firstName}
        value={data.firstName}
        onChange={(e) => onChange('firstName', e.target.value)}
        error={!!errors.firstName}
        helperText={errors.firstName}
        onFocus={() => accessibility.voiceGuidance && voiceGuidance.speak(t.firstName)}
      />
    </Grid>
    
    <Grid item xs={12} sm={6}>
      <TextField
        fullWidth
        required
        label={t.lastName}
        value={data.lastName}
        onChange={(e) => onChange('lastName', e.target.value)}
        error={!!errors.lastName}
        helperText={errors.lastName}
        onFocus={() => accessibility.voiceGuidance && voiceGuidance.speak(t.lastName)}
      />
    </Grid>
    
    <Grid item xs={12} sm={6}>
      <TextField
        fullWidth
        required
        label={t.dateOfBirth}
        type="date"
        value={data.dateOfBirth}
        onChange={(e) => onChange('dateOfBirth', e.target.value)}
        error={!!errors.dateOfBirth}
        helperText={errors.dateOfBirth}
        InputLabelProps={{ shrink: true }}
      />
    </Grid>
    
    <Grid item xs={12} sm={6}>
      <FormControl fullWidth required error={!!errors.gender}>
        <FormLabel component="legend">{t.gender}</FormLabel>
        <RadioGroup
          row
          value={data.gender}
          onChange={(e) => onChange('gender', e.target.value)}
        >
          <FormControlLabel value="male" control={<Radio />} label="Male" />
          <FormControlLabel value="female" control={<Radio />} label="Female" />
          <FormControlLabel value="other" control={<Radio />} label="Other" />
        </RadioGroup>
      </FormControl>
    </Grid>
  </Grid>
);

const ContactStep: React.FC<any> = ({ data, onChange, errors, t, accessibility }) => (
  <Grid container spacing={2}>
    <Grid item xs={12} sm={6}>
      <TextField
        fullWidth
        required
        label={t.phoneNumber}
        value={data.phoneNumber}
        onChange={(e) => onChange('phoneNumber', e.target.value)}
        error={!!errors.phoneNumber}
        helperText={errors.phoneNumber}
      />
    </Grid>
    
    <Grid item xs={12} sm={6}>
      <TextField
        fullWidth
        label={t.email}
        type="email"
        value={data.email}
        onChange={(e) => onChange('email', e.target.value)}
        error={!!errors.email}
        helperText={errors.email || t.optional}
      />
    </Grid>
    
    <Grid item xs={12}>
      <TextField
        fullWidth
        label={t.address}
        multiline
        rows={2}
        value={data.address}
        onChange={(e) => onChange('address', e.target.value)}
        helperText={t.optional}
      />
    </Grid>
  </Grid>
);

const MedicalHistoryStep: React.FC<any> = ({ data, onArrayAdd, onArrayRemove, onChange, t }) => (
  <Grid container spacing={2}>
    <Grid item xs={12}>
      <ArrayInputField
        label={t.allergies}
        values={data.allergies}
        onAdd={(value) => onArrayAdd('allergies', value)}
        onRemove={(value) => onArrayRemove('allergies', value)}
        placeholder="Enter allergy and press Enter"
      />
    </Grid>
    
    <Grid item xs={12}>
      <ArrayInputField
        label={t.medications}
        values={data.currentMedications}
        onAdd={(value) => onArrayAdd('currentMedications', value)}
        onRemove={(value) => onArrayRemove('currentMedications', value)}
        placeholder="Enter medication and press Enter"
      />
    </Grid>
    
    <Grid item xs={12}>
      <ArrayInputField
        label={t.conditions}
        values={data.medicalConditions}
        onAdd={(value) => onArrayAdd('medicalConditions', value)}
        onRemove={(value) => onArrayRemove('medicalConditions', value)}
        placeholder="Enter medical condition and press Enter"
      />
    </Grid>
    
    <Grid item xs={12}>
      <TextField
        fullWidth
        label={t.insurance}
        value={data.insuranceInfo}
        onChange={(e) => onChange('insuranceInfo', e.target.value)}
        helperText={t.optional}
      />
    </Grid>
  </Grid>
);

const EmergencyContactStep: React.FC<any> = ({ data, onChange, errors, t }) => (
  <Grid container spacing={2}>
    <Grid item xs={12} sm={6}>
      <TextField
        fullWidth
        label={t.emergencyContact}
        value={data.emergencyContactName}
        onChange={(e) => onChange('emergencyContactName', e.target.value)}
        helperText={t.optional}
      />
    </Grid>
    
    <Grid item xs={12} sm={6}>
      <TextField
        fullWidth
        label={t.emergencyPhone}
        value={data.emergencyContactPhone}
        onChange={(e) => onChange('emergencyContactPhone', e.target.value)}
        helperText={t.optional}
      />
    </Grid>
    
    <Grid item xs={12}>
      <TextField
        fullWidth
        label={t.relationship}
        value={data.emergencyContactRelationship}
        onChange={(e) => onChange('emergencyContactRelationship', e.target.value)}
        helperText={t.optional}
      />
    </Grid>
  </Grid>
);

const ConsentStep: React.FC<any> = ({ data, onChange, errors, t }) => (
  <Box>
    <Alert severity="info" sx={{ mb: 2 }}>
      <AlertTitle>Consent and Privacy</AlertTitle>
      Please review and agree to the following consent statements before proceeding.
    </Alert>
    
    <FormControlLabel
      control={
        <Checkbox
          checked={data.consentTreatment}
          onChange={(e) => onChange('consentTreatment', e.target.checked)}
          color="primary"
        />
      }
      label={
        <Typography variant="body2">
          {t.consentTreatment} - I understand and consent to receive medical treatment and assessment.
        </Typography>
      }
      sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}
    />
    
    <FormControlLabel
      control={
        <Checkbox
          checked={data.consentDataProcessing}
          onChange={(e) => onChange('consentDataProcessing', e.target.checked)}
          color="primary"
        />
      }
      label={
        <Typography variant="body2">
          {t.consentData} - I consent to the processing of my personal health information for healthcare purposes in accordance with privacy regulations.
        </Typography>
      }
      sx={{ display: 'flex', alignItems: 'flex-start' }}
    />
    
    {(errors.consentTreatment || errors.consentDataProcessing) && (
      <Alert severity="error" sx={{ mt: 2 }}>
        Both consent agreements are required to proceed with registration.
      </Alert>
    )}
  </Box>
);

// Accessibility Controls Component
const AccessibilityControls: React.FC<any> = ({ settings, onChange, t }) => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Tooltip title={t.accessibility}>
        <IconButton onClick={() => setOpen(true)}>
          <AccessibilityIcon />
        </IconButton>
      </Tooltip>
      
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t.accessibility}</DialogTitle>
        <DialogContent>
          <List>
            <ListItem>
              <ListItemText primary={t.voiceGuidance} />
              <Switch
                checked={settings.voiceGuidance}
                onChange={(e) => onChange(prev => ({ ...prev, voiceGuidance: e.target.checked }))}
              />
            </ListItem>
            
            <ListItem>
              <ListItemText primary="Large Text" />
              <Switch
                checked={settings.largeText}
                onChange={(e) => onChange(prev => ({ ...prev, largeText: e.target.checked }))}
              />
            </ListItem>
            
            <ListItem>
              <ListItemText primary="High Contrast" />
              <Switch
                checked={settings.highContrast}
                onChange={(e) => onChange(prev => ({ ...prev, highContrast: e.target.checked }))}
              />
            </ListItem>
            
            <ListItem>
              <ListItemText primary="Voice Input" />
              <Switch
                checked={settings.voiceInput}
                onChange={(e) => onChange(prev => ({ ...prev, voiceInput: e.target.checked }))}
              />
            </ListItem>
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

// Array Input Field Component
const ArrayInputField: React.FC<any> = ({ label, values, onAdd, onRemove, placeholder }) => {
  const [inputValue, setInputValue] = useState('');

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault();
      onAdd(inputValue.trim());
      setInputValue('');
    }
  };

  return (
    <Box>
      <TextField
        fullWidth
        label={label}
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder={placeholder}
        helperText="Press Enter to add items"
      />
      
      <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {values.map((value: string, index: number) => (
          <Chip
            key={index}
            label={value}
            onDelete={() => onRemove(value)}
            color="primary"
            variant="outlined"
          />
        ))}
      </Box>
    </Box>
  );
};

export default PatientRegistrationForm;
