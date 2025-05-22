"use client";

import React, { useState, useEffect } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { FilterCard } from "./FilterCard";


const ALL_TRAFFIC = [
    { id: "Large", label: "大型" },
    { id: "Car", label: "車" },
    { id: "Bike", label: "二輪車" },
    { id: "Bike", label: "自転車" },
  ];

  interface TrafficFilterProps {
    initialSelectedTraffic?: string[];
    onSelectionChange?: (selectedTraffic: string[]) => void;
  }

  export function TrafficFilter({ initialSelectedTraffic, onSelectionChange }: TrafficFilterProps){
    const [selectedTraffic, setselectedTraffic] = useState<string[]>(initialSelectedTraffic || ALL_TRAFFIC.map(g => g.id));
    const [isAllSelected, setIsAllSelected] = useState(selectedTraffic.length === ALL_TRAFFIC.length);

    useEffect(() => {    

        setIsAllSelected(selectedTraffic.length === ALL_TRAFFIC.length);
        if (onSelectionChange) {
            onSelectionChange(selectedTraffic);
          }
        }, [selectedTraffic, onSelectionChange]);
    
        const handleTrafficToggle = (trafficId: string) => {
            setselectedTraffic((prevSelected) =>
              prevSelected.includes(trafficId)
                ? prevSelected.filter((g) => g !== trafficId)
                : [...prevSelected, trafficId]
            );
          };

          const handleSelectAllToggle = () => {
            if (isAllSelected) {
                setselectedTraffic([]);
            } else {
                setselectedTraffic(ALL_TRAFFIC.map(g => g.id));
            }
          };

          return (
            <FilterCard title="交通">
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="select-all-traffic"
                    checked={isAllSelected}
                    onCheckedChange={handleSelectAllToggle}
                  />
                  <Label htmlFor="select-all-genders" className="text-sm font-medium">
                    すべて
                  </Label>
                </div>
                {ALL_TRAFFIC.map((traffic) => (
                  <div key={traffic.id} className="flex items-center space-x-2">
                    <Checkbox
                      id={traffic.id}
                      checked={selectedTraffic.includes(traffic.id)}
                      onCheckedChange={() => handleTrafficToggle(traffic.id)}
                    />
                    <Label htmlFor={traffic.id} className="text-sm font-normal">
                      {traffic.label}
                    </Label>
                  </div>
                ))}
              </div>
            </FilterCard>
          );          
  }

