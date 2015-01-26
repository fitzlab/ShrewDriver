package com.example.stimbot;

import javax.microedition.khronos.opengles.GL10;

public class RenderedObject {

	/*
	 * Rendered Objects include the stim and the aperture. This class holds information about
	 * the position, angle, and textures of rendered objects, e.g. apertures and gratings.
	 * 
	 * Mostly it just handles all the unit conversion involved, details follow.
	 * 
	 * ==============
	 * Stim Placement
	 * ==============
	 * 
	 * There are four different units with which you could talk about stim placement. (Yeah, I know.)
	 * 
	 * OPENGL COORDINATES:
	 * These start at the bottom-left of the screen (0.0, 0.0) and go up to the top-right (1.0, 1.0).
	 * 
	 * VISUAL DEGREES: 
	 * These start at the center of the screen (0,0). The top-right corner is (+x, +y). 
	 * 
	 * MILLIMETERS:
	 * OpenGL coordinates, but in millimeters instead. An intermediate between the two settings above.
	 * 
	 * PIXELS:
	 * Yeah, we don't use this.
	 * 
	 * ===========
	 * Orientation
	 * ===========
	 * 
	 * There are two ways to talk about orientation: There's the right way, aaaaand there's the way our lab uses.
	 * Orientation in OpenGL starts at horizontal and runs counterclockwise (which is standard generally).
	 * Orientation in our lab starts horizontal and runs clockwise (wtf). 
	 * Inputs are assumed to be in lab orientation; this class will convert it to OpenGL here.
	 * 
	 * =====
	 * Phase
	 * =====
	 * 
	 * Grating phase is randomized on each grating presentation by a call to randomizePhase(). 
	 * This is desirable in most applications.
	 * 
	 */

	/* ---- Input values ---- */
	
	private float screenDistanceMillis = 1000.0f; //must be set by function call

	public float centerXDegrees = 0.0f;
	public float centerYDegrees = 0.0f;
	
	public float sizeXDegrees = 7.0f;
	public float sizeYDegrees = 7.0f;
	
	public float objectOrientation = 0.0f; // lab standard, 0=horizontal, + = clockwise rotation. 
	
	//params below are for gratings only
	public float gratingOrientation = 135.0f; // lab standard, 0=horizontal, + = clockwise rotation. 
	public float spatialFrequency = 1.0f;
	public float temporalFrequency = 1.0f;
	public float jitterFrequency = 0.0f;
	public float jitterAmount = 0.0f;
	
	/* ---- Constants ---- */
	
	//nexus screen properties
	private float nexusScreenWidthPx = 2560;
	private float nexusScreenHeightPx = 1600;
	private float nexusScreenWidthMillis = 216.6f; //yes, the pixels are perfect squares so we
	private float nexusScreenHeightMillis = 135.36f; //don't need to correct for that.

	/* ---- Computed values ---- */
	float screenHeightDegrees;
	float screenWidthDegrees;
	
	//These are values that OpenGL will use when drawing the object.
	public float scaleX = 1.0f;
	public float scaleY = 1.0f;
	public float scaleZ = 1.0f;
	
	public float angleX = 0.0f;
	public float angleY = 0.0f;
	public float angleZ = 0.0f;

	public float posX = 0.0f;
	public float posY = 0.0f;
	public float posZ = 0.0f;
	
	//the ones below only apply to gratings
	public float texturePosX = 0.0f;
	public float texturePosY = 0.0f;
	public float texturePosZ = 0.0f;
	
	public float textureScaleX = 1.0f;
	public float textureScaleY = 1.0f;
	public float textureScaleZ = 1.0f;
	
	public float textureAngleX = 0.0f;
	public float textureAngleY = 0.0f;
	public float textureAngleZ = 0.0f;

	private float texturePosXBeforeJitter = 0.0f;
	private float jitterPhase = 0.0f;
	
	/* ---- State ---- */
	private long prevTimeNanos = -1; 

	/* ---- Constructors ---- */
	public RenderedObject(){
		//calculate all the default values, just in case the user doesn't provide anything
		setScreenDistanceMillis(screenDistanceMillis);
		computeParams();
	}

	/* ---- Called each frame ---- */
	public void computeParams(){
		//scaling
		//note that the base object size is a square of dimensions equal to the screen height.
		scaleX = sizeXDegrees / screenWidthDegrees;
		scaleY = sizeYDegrees / screenHeightDegrees;
		
		//orientation
		angleZ = -objectOrientation;
		
		//position
		posX = centerXDegrees / screenWidthDegrees;
		posY = centerYDegrees / screenHeightDegrees;
		
		//texture position
		//only X matters, because it's a grating and rotation + scaling are handled after position
		if(prevTimeNanos == -1){
			prevTimeNanos = System.nanoTime();
		}

		long timeNanos = System.nanoTime();
		float timeDifferenceSeconds = (float) ((timeNanos-prevTimeNanos) / 1000000000.0);
		if(temporalFrequency > 0.0){
			texturePosXBeforeJitter -= timeDifferenceSeconds * temporalFrequency;
		}
		if(jitterFrequency > 0.0){
			jitterPhase = (jitterPhase + timeDifferenceSeconds * jitterFrequency) % 1;
			
			float jitterPos = jitterPhase;
			if(jitterPos < 0.5){
				jitterPos = 1.0f-jitterPos;
			}
			texturePosX = texturePosXBeforeJitter + jitterPos * jitterAmount;
		}
		else{
			texturePosX = texturePosXBeforeJitter;
		}
		prevTimeNanos = timeNanos;
		
		//texture scaling
		textureScaleX = spatialFrequency * sizeXDegrees;
		textureScaleY = spatialFrequency * sizeYDegrees;
		
		//texture rotation
		textureAngleZ = 90.0f - gratingOrientation;
		
	}
	
	
	/* ---- Setters ---- */
	public void setPhase(float phase){
		texturePosXBeforeJitter = phase;
	}
	
	public void setScreenDistanceMillis(float screenDistanceMillis){
		this.screenDistanceMillis = screenDistanceMillis;
		
		//Converting screen width into visual degrees is actually more complex than it seems, since screens are rectangles.
		//As you get closer to a rectangle, it grows faster horizontally than it does vertically. To convince yourself
		//of this, try holding a pen in horizontally in front of you and moving it closer / further from your eye. 
		
		//Therefore, degrees are (arbitrarily) based on the height of the screen. It had to be one dimension, 
		//might as well be that. That seems to be the standard in PsychoPy and Psychtoolbox as well.
		
		//compute screen size in visual degrees based on distance from eye to screen
		double screenHeightRadians = Math.atan((this.nexusScreenHeightMillis/2) / this.screenDistanceMillis) * 2;
		screenHeightDegrees = (float) (screenHeightRadians * 180.0 / Math.PI);
		
		//not doing this...
		/*double screenWidthRadians = Math.atan((this.nexusScreenWidthMillis/2) / this.screenDistanceMillis) * 2;
		screenWidthDegrees = (float) (screenWidthRadians * 180.0 / Math.PI);*/

		//doing this instead!
		screenWidthDegrees = screenHeightDegrees * nexusScreenWidthMillis / nexusScreenHeightMillis;
		
		//recompute other object params
		computeParams();
	}

	public void setTemporalFrequency(float temporalFrequency){
		this.temporalFrequency = temporalFrequency;
		computeParams();
	}

	public void setObjectOrientation(float objectOrientation){
		this.objectOrientation = objectOrientation;
		computeParams();
	}

	public void setGratingOrientation(float gratingOrientation){
		this.gratingOrientation = gratingOrientation;
		computeParams();
	}

	public void setCenterDegrees(float centerXDegrees, float centerYDegrees){
		this.centerXDegrees = centerXDegrees;
		this.centerYDegrees = centerYDegrees;
		computeParams();
	}
	
	public void setSizeDegrees(float sizeXDegrees, float sizeYDegrees){
		this.sizeXDegrees = sizeXDegrees;
		this.sizeYDegrees = sizeYDegrees;
		computeParams();
	}
    
}