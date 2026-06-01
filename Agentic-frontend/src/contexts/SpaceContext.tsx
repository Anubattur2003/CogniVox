import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Space, spaceApi } from '../services/api';
import { toast } from 'react-hot-toast';
import { useAuth } from './AuthContext';

interface SpaceContextType {
  spaces: Space[];
  selectedSpace: Space | null;
  loading: boolean;
  setSelectedSpace: (space: Space | null) => void;
  fetchSpaces: () => Promise<void>;
  createSpace: (data: { name: string; description?: string; color?: string; icon?: string }) => Promise<Space | null>;
  updateSpace: (spaceId: string, data: Partial<Space>) => Promise<void>;
  deleteSpace: (spaceId: string) => Promise<void>;
  setDefaultSpace: (spaceId: string) => Promise<void>;
}

const SpaceContext = createContext<SpaceContextType | undefined>(undefined);

export const SpaceProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [spaces, setSpaces] = useState<Space[]>([]); // Always initialize as empty array
  const [selectedSpace, setSelectedSpaceState] = useState<Space | null>(null);
  const [loading, setLoading] = useState(false);
  const { isAuthenticated } = useAuth();

  // Load spaces on mount and when authentication changes
  useEffect(() => {
    if (isAuthenticated) {
      fetchSpaces();
      
      // Load selected space from localStorage
      const savedSpaceId = localStorage.getItem('selectedSpaceId');
      if (savedSpaceId) {
        // We'll set it after spaces are loaded
      }
    } else {
      setSpaces([]);
      setSelectedSpaceState(null);
    }
  }, [isAuthenticated]);

  // Set selected space from localStorage after spaces are loaded
  useEffect(() => {
    if (spaces.length > 0 && !selectedSpace) {
      const savedSpaceId = localStorage.getItem('selectedSpaceId');
      if (savedSpaceId) {
        const space = spaces.find(s => s.id === savedSpaceId);
        if (space) {
          setSelectedSpaceState(space);
        } else {
          // Clear invalid saved space ID
          localStorage.removeItem('selectedSpaceId');
        }
      }
    }
  }, [spaces]);

  const fetchSpaces = async (): Promise<void> => {
    try {
      setLoading(true);
      console.log('Fetching spaces from backend...');
      const response = await spaceApi.getSpaces();
      
      if (response.data && response.status === 200) {
        // Handle both paginated and non-paginated responses
        const spacesData = (response.data as any).results || response.data;
        console.log('Spaces fetched successfully:', Array.isArray(spacesData) ? spacesData.length : 0, 'spaces');
        console.log('Space data with counts:', spacesData);
        setSpaces(Array.isArray(spacesData) ? spacesData : []);
        
        // Update selectedSpace if it exists to get fresh data including updated thread_count
        if (selectedSpace && Array.isArray(spacesData)) {
          const updatedSelectedSpace = spacesData.find((s: any) => s.id === selectedSpace.id);
          if (updatedSelectedSpace) {
            setSelectedSpaceState(updatedSelectedSpace);
          }
        }
      } else {
        console.error('Failed to fetch spaces:', response.error);
        toast.error('Failed to load spaces');
        setSpaces([]);
      }
    } catch (error) {
      console.error('Error fetching spaces:', error);
      toast.error('Failed to load spaces');
      setSpaces([]);
    } finally {
      setLoading(false);
    }
  };

  const createSpace = async (data: { name: string; description?: string; color?: string; icon?: string }): Promise<Space | null> => {
    try {
      const response = await spaceApi.createSpace(data);
      
      if (response.data && (response.status === 200 || response.status === 201)) {
        const newSpace = response.data;
        console.log('Space created successfully:', newSpace);
        toast.success('Space created successfully');
        // Re-fetch all spaces to get accurate thread counts
        await fetchSpaces();
        return newSpace;
      } else {
        toast.error(response.error || 'Failed to create space');
        return null;
      }
    } catch (error) {
      console.error('Error creating space:', error);
      toast.error('Failed to create space');
      return null;
    }
  };

  const updateSpace = async (spaceId: string, data: Partial<Space>) => {
    try {
      const response = await spaceApi.updateSpace(spaceId, data);
      
      if (response.data && response.status === 200) {
        setSpaces(prev => {
          const currentSpaces = Array.isArray(prev) ? prev : [];
          return currentSpaces.map(s => s.id === spaceId ? response.data! : s);
        });
        
        // Update selected space if it's the one being updated
        if (selectedSpace?.id === spaceId) {
          setSelectedSpaceState(response.data);
        }
        
        toast.success('Space updated successfully');
      } else {
        toast.error(response.error || 'Failed to update space');
      }
    } catch (error) {
      console.error('Error updating space:', error);
      toast.error('Failed to update space');
    }
  };

  const deleteSpace = async (spaceId: string) => {
    try {
      const response = await spaceApi.deleteSpace(spaceId);
      
      if (response.status === 200 || response.status === 204) {
        setSpaces(prev => {
          const currentSpaces = Array.isArray(prev) ? prev : [];
          return currentSpaces.filter(s => s.id !== spaceId);
        });
        
        // Clear selected space if it's the one being deleted
        if (selectedSpace?.id === spaceId) {
          setSelectedSpaceState(null);
          localStorage.removeItem('selectedSpaceId');
        }
        
        toast.success('Space deleted successfully');
      } else {
        toast.error(response.error || 'Failed to delete space');
      }
    } catch (error) {
      console.error('Error deleting space:', error);
      toast.error('Failed to delete space');
    }
  };

  const setDefaultSpace = async (spaceId: string) => {
    try {
      const response = await spaceApi.setDefaultSpace(spaceId);
      
      if (response.status === 200) {
        // Update spaces to reflect new default
        setSpaces(prev => {
          const currentSpaces = Array.isArray(prev) ? prev : [];
          return currentSpaces.map(s => ({
            ...s,
            is_default: s.id === spaceId
          }));
        });
        
        toast.success('Default space set');
      } else {
        toast.error(response.error || 'Failed to set default space');
      }
    } catch (error) {
      console.error('Error setting default space:', error);
      toast.error('Failed to set default space');
    }
  };

  const setSelectedSpace = (space: Space | null) => {
    setSelectedSpaceState(space);
    
    // Save to localStorage
    if (space) {
      localStorage.setItem('selectedSpaceId', space.id);
    } else {
      localStorage.removeItem('selectedSpaceId');
    }
  };

  return (
    <SpaceContext.Provider
      value={{
        spaces,
        selectedSpace,
        loading,
        setSelectedSpace,
        fetchSpaces,
        createSpace,
        updateSpace,
        deleteSpace,
        setDefaultSpace,
      }}
    >
      {children}
    </SpaceContext.Provider>
  );
};

export const useSpace = () => {
  const context = useContext(SpaceContext);
  if (context === undefined) {
    throw new Error('useSpace must be used within a SpaceProvider');
  }
  return context;
};

