// Simple test file to verify TypeScript compilation
import React from 'react';
import { PatientRegistrationForm } from './components/PatientRegistration';
import DeviceIntegration from './components/DeviceIntegration';

const TestComponent: React.FC = () => {
  return (
    <div>
      <h1>Smart Triage Kiosk System</h1>
      <p>This is a test to verify TypeScript compilation is working.</p>
      {/* These components should compile without errors */}
      {process.env.NODE_ENV === 'test' && (
        <>
          <PatientRegistrationForm />
          <DeviceIntegration />
        </>
      )}
    </div>
  );
};

export default TestComponent;
