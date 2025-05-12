import { Device, DeviceCreateData, DeviceUpdateData } from '@/types/device';

export const deviceService = {
  // Get all devices
  async getDevices(): Promise<Device[]> {
    const response = await fetch('/api/devices');
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch devices');
    }
    
    return response.json();
  },

  // Get a single device by ID
  async getDevice(id: string): Promise<Device | null> {
    const response = await fetch(`/api/devices/${id}`);
    
    if (response.status === 404) {
      return null;
    }
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch device');
    }
    
    return response.json();
  },
  
  // Create a new device
  async createDevice(data: DeviceCreateData): Promise<Device> {
    // Clean up empty fields to avoid backend validation issues
    const cleanData = { ...data };
    Object.keys(cleanData).forEach((key) => {
      if (cleanData[key as keyof DeviceCreateData] === '') {
        delete cleanData[key as keyof DeviceCreateData];
      }
    });
    
    const response = await fetch('/api/devices', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cleanData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create device');
    }
    
    return response.json();
  },
  
  // Update an existing device
  async updateDevice(id: string, data: DeviceUpdateData): Promise<Device> {
    const response = await fetch(`/api/devices/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update device');
    }
    
    return response.json();
  },

    
  // Execute device actions (provision, activate, decommission)
  async executeDeviceAction(id: string, action: string): Promise<Device> {
    const response = await fetch(`/api/devices/${id}/${action}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Failed to execute ${action}`);
    }
    
    return response.json();
  }

}