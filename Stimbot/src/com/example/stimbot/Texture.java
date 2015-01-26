package com.example.stimbot;

import javax.microedition.khronos.opengles.GL10;

import android.graphics.Bitmap;
import android.opengl.GLUtils;

public class Texture {

	public int index = -1; //-1 for unassigned, >=0 otherwise
	public Bitmap bitmap; //the texture data itself
	public String name = ""; //e.g. "gabor", "black", "grating"
	
	public Texture(Bitmap bitmap_, int index_){
		bitmap = bitmap_;
		index = index_; 
	 	GLUtils.texImage2D(GL10.GL_TEXTURE_2D, 0, bitmap, 0);
	}
}
