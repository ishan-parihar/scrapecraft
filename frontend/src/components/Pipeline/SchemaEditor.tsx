import React, { useState, useEffect } from 'react';
 import { useInvestigationStore } from '../../store/investigationStore';
import Button from '../Common/Button';
import Input from '../Common/Input';

interface SchemaField {
  name: string;
  type: string;
  description: string;
}

const SchemaEditor: React.FC = () => {
  const { currentInvestigation, updateInvestigation } = useInvestigationStore();
  const [fields, setFields] = useState<SchemaField[]>([]);
  const [newField, setNewField] = useState<SchemaField>({
    name: '',
    type: 'str',
    description: ''
  });

  useEffect(() => {
    // For investigations, we can use intelligence requirements as schema
    // This is a placeholder - in a real implementation you might use intelligence requirements
    // or other investigation properties as the schema equivalent
    if (currentInvestigation?.intelligence_requirements) {
      // Create schema from intelligence requirements
      const schemaFields = currentInvestigation.intelligence_requirements.map((req, index) => ({
        name: req.requirement.substring(0, 20) + (req.requirement.length > 20 ? '...' : ''), // Shorten for display
        type: req.category,
        description: req.requirement
      }));
      setFields(schemaFields);
    }
  }, [currentInvestigation?.intelligence_requirements]);

  const handleAddField = () => {
    if (!newField.name.trim() || !currentInvestigation) return;

    const updatedFields = [...fields, newField];
    setFields(updatedFields);
    
    // Update investigation with new intelligence requirement
    const newIntelligenceRequirement = {
      id: `req_${Date.now()}`,
      requirement: newField.description || newField.name,
      priority: 'MEDIUM' as const,
      category: 'OTHER' as const,
      source_type: 'COMBINED' as const,
      status: 'PENDING' as const,
      evidence_collected: []
    };
    
    updateInvestigation(currentInvestigation.id, {
      ...currentInvestigation,
      intelligence_requirements: [
        ...currentInvestigation.intelligence_requirements, 
        newIntelligenceRequirement
      ]
    });
    
    // Reset form
    setNewField({ name: '', type: 'str', description: '' });
  };

  const handleRemoveField = (index: number) => {
    if (!currentInvestigation) return;
    
    const updatedFields = fields.filter((_, i) => i !== index);
    setFields(updatedFields);
    
    // Update investigation by removing the corresponding intelligence requirement
    const updatedRequirements = currentInvestigation.intelligence_requirements.filter((_, i) => i !== index);
    
    updateInvestigation(currentInvestigation.id, {
      ...currentInvestigation,
      intelligence_requirements: updatedRequirements
    });
  };

  const fieldTypes = [
    { value: 'str', label: 'String' },
    { value: 'int', label: 'Integer' },
    { value: 'float', label: 'Float' },
    { value: 'bool', label: 'Boolean' },
    { value: 'list', label: 'List' },
    { value: 'dict', label: 'Dictionary' }
  ];

  return (
    <div className="h-full flex flex-col p-4">
       <h3 className="text-lg font-semibold mb-4">Intelligence Requirements</h3>
      
      {/* Add Field Form */}
      <div className="space-y-3 mb-4 card">
        <div className="grid grid-cols-3 gap-2">
           <Input
             value={newField.name}
             onChange={(e) => setNewField({ ...newField, name: e.target.value })}
             placeholder="Requirement name"
             disabled={!currentInvestigation}
           />
          
          <select
            value={newField.type}
            onChange={(e) => setNewField({ ...newField, type: e.target.value })}
            className="input"
             disabled={!currentInvestigation}
           >
            {fieldTypes.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          
          <Button
            onClick={handleAddField}
             disabled={!newField.name.trim() || !currentInvestigation}
            variant="primary"
          >
            Add Field
          </Button>
        </div>
        
           <Input
             value={newField.description}
             onChange={(e) => setNewField({ ...newField, description: e.target.value })}
             placeholder="Intelligence requirement description (optional)"
             disabled={!currentInvestigation}
           />
      </div>
      
      {/* Fields List */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {fields.length === 0 ? (
           <div className="text-center text-muted py-8">
             <p>No intelligence requirements defined</p>
             <p className="text-sm mt-2">Add requirements to define what intelligence to collect</p>
           </div>
        ) : (
          fields.map((field, index) => (
            <div key={index} className="card flex items-center justify-between">
              <div>
                <div className="font-medium">{field.name}</div>
                <div className="text-sm text-muted">
                  Type: {fieldTypes.find(t => t.value === field.type)?.label || field.type}
                  {field.description && ` • ${field.description}`}
                </div>
              </div>
              
              <Button
                variant="destructive"
                size="sm"
                onClick={() => handleRemoveField(index)}
              >
                Remove
              </Button>
            </div>
          ))
        )}
      </div>
      
      {/* JSON Preview */}
      {fields.length > 0 && (
         <div className="mt-4 p-3 bg-code-bg rounded-md">
           <div className="text-xs text-muted mb-2">Intelligence Requirements Preview:</div>
           <pre className="text-xs text-code-text">
             {JSON.stringify(
               fields.reduce((acc, field, index) => ({
                 ...acc,
                 [field.name]: {
                   type: field.type,
                   description: field.description
                 }
               }), {}),
               null,
               2
             )}
           </pre>
         </div>
      )}
    </div>
  );
};

export default SchemaEditor;