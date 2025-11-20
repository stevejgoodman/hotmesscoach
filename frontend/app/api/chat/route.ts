import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Forward the request to FastAPI backend
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: body.message,
        model: body.model || 'gpt-4o-mini',
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend API error:', errorText);
      return NextResponse.json(
        { error: 'Failed to get response from backend', details: errorText },
        { status: response.status }
      );
    }

    // Handle image responses
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.startsWith('image/')) {
      const imageBuffer = await response.arrayBuffer();
      return new NextResponse(imageBuffer, {
        headers: {
          'Content-Type': contentType,
        },
      });
    }

    // Handle JSON responses
    const data = await response.json();
    
    // Transform backend response to match frontend expectations
    // Backend returns { "reply": ... } or { "error": ... }
    return NextResponse.json({
      response: data.reply || data.response || data.message || (data.error ? `Error: ${data.error}` : JSON.stringify(data)),
    });
  } catch (error) {
    console.error('Error in chat API route:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}

