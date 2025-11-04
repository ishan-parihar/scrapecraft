# Fix for New Investigation Button

## Problem
The "New Investigation" button in the Header component was not working because it lacked an `onClick` event handler.

## Solution
Added the necessary functionality to the Header component to:

1. Import the `useInvestigationStore` hook to access the investigation creation function
2. Add a click handler function `handleNewInvestigation` that calls the store's `createInvestigation` method
3. Add the `onClick` prop to the "New Investigation" button to trigger the handler

## Code Changes

### File: `src/components/Layout/Header.tsx`

- Added import for `useInvestigationStore`
- Added state management for settings modal
- Implemented `handleNewInvestigation` function to create a new investigation with default values
- Connected the "New Investigation" button to the handler function

## Technical Details

The fix leverages the existing investigation store functionality:
- Uses the same store that manages all investigation state
- Creates investigations with appropriate default values
- Updates the current investigation in the store, which automatically triggers UI updates
- Maintains consistency with the existing architecture

## Default Values for New Investigations
- Title: "New OSINT Investigation"
- Description: "Conducting intelligence assessment"
- Classification: "UNCLASSIFIED" 
- Priority: "MEDIUM"

## Result
The "New Investigation" button now successfully creates new investigations and updates the UI accordingly.