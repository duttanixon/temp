export interface Position {
    x: number;
    y: number;
}

export interface Vertex {
    vertexId: string;
    position: Position;
}

export interface Point {
    lat: number;
    lng: number;
}

export interface Center {
    startPoint: Point;
    endPoint: Point;
}

export interface DetectionZone {
    polygonId: string;
    name: string;
    vertices: Vertex[];
    center: Center;
}

export interface XLinesConfigPayload {
    device_id: string;
    detectionZones: DetectionZone[];
}
  
export interface PolygonCommandResponse {
    device_name: string;
    message_id: string;
    detail: string;
  }

export interface Route {
    center: {
      startPoint: Point;
      endPoint: Point;
    }
}

export type Polygon = {
    polygonId: string;
    name: string;
    vertices: Vertex[];
  };

export type PolygonState = {
    visible: boolean;
    active: boolean;
  };

export type PolygonStates = Record<string, PolygonState>;

export type PolygonWithRoute = Polygon & Route;