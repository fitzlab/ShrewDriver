package com.example.stimbot;

import javax.microedition.khronos.opengles.GL10;

import android.graphics.Bitmap;
import android.opengl.GLUtils;


//Just moving crap out of MyRenderer for now. Make this nicer later!

public class TextureFactory {

	public int numTextures = 0;

	//This is an equal-luminant gray (or very close -- double check with a photodiode later.)
	private int grayVal = 180; 

    // STIM TEXTURES
	public Texture blackTexture(){
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
    	Bitmap b = Bitmap.createBitmap(1, 1, conf);
		int pxVal = ((0xff) << 24)
				  | ((0 & 0xff) << 16)
				  | ((0 & 0xff) << 8)
				  | ((0 & 0xff));
		b.setPixel(0, 0, pxVal);

        Texture tx = new Texture(b, numTextures);
        tx.name = "black";
        numTextures++;
        return tx;
    }
    
    public Texture whiteTexture(){
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
    	Bitmap b = Bitmap.createBitmap(1, 1, conf);
		int pxVal = ((0xff) << 24)
				  | ((0xff) << 16)
				  | ((0xff) << 8)
				  | ((0xff));
		b.setPixel(0, 0, pxVal);

        Texture tx = new Texture(b, numTextures);
        tx.name = "white";
        numTextures++;
        return tx;
    }

    public Texture grayTexture(){
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
    	Bitmap b = Bitmap.createBitmap(1, 1, conf);
		int pxVal = ((0xff) << 24)
			  | ((grayVal & 0xff) << 16)
			  | ((grayVal & 0xff) << 8)
			  | ((grayVal & 0xff));
		b.setPixel(0, 0, pxVal);

        Texture tx = new Texture(b, numTextures);
        tx.name = "gray";
        numTextures++;
        return tx;
    }

    public Texture redTexture(){
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
    	Bitmap b = Bitmap.createBitmap(1, 1, conf);
		int pxVal = ((0xff) << 24)
				  | ((0 & 0xff) << 16) //B
				  | ((0 & 0xff) << 8)  //G
				  | ((0xff));  //R
		b.setPixel(0, 0, pxVal);

        Texture tx = new Texture(b, numTextures);
        tx.name = "red";
        numTextures++;
        return tx;
    }

    public Texture greenTexture(){
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
    	Bitmap b = Bitmap.createBitmap(1, 1, conf);
		int pxVal = ((0xff) << 24)
				  | ((0 & 0xff) << 16) //B
				  | ((0xff) << 8)  //G
				  | ((0 & 0xff));  //R
		b.setPixel(0, 0, pxVal);

        Texture tx = new Texture(b, numTextures);
        tx.name = "green";
        numTextures++;
        return tx;
    } 
    
    public Texture blueTexture(){
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
    	Bitmap b = Bitmap.createBitmap(1, 1, conf);
		int pxVal = ((0xff) << 24)
				  | ((0xff) << 16) //B
				  | ((0 & 0xff) << 8)  //G
				  | ((0 & 0xff));  //R
		b.setPixel(0, 0, pxVal);

        Texture tx = new Texture(b, numTextures);
        tx.name = "blue";
        numTextures++;
        return tx;
    }
    
    public Texture yellowTexture(){
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
    	Bitmap b = Bitmap.createBitmap(1, 1, conf);
		int pxVal = ((0xff) << 24)
				  | ((0 & 0xff) << 16) //B
				  | ((0xff) << 8)  //G
				  | ((0xff));  //R
		b.setPixel(0, 0, pxVal);

        Texture tx = new Texture(b, numTextures);
        tx.name = "yellow";
        numTextures++;
        return tx;
    }

    public Texture cyanTexture(){
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
    	Bitmap b = Bitmap.createBitmap(1, 1, conf);
		int pxVal = ((0xff) << 24)
				  | ((0xff) << 16) //B
				  | ((0xff) << 8)  //G
				  | ((0 & 0xff));  //R
		b.setPixel(0, 0, pxVal);

        Texture tx = new Texture(b, numTextures);
        tx.name = "cyan";
        numTextures++;
        return tx;
    } 
    
    public Texture magentaTexture(){
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
    	Bitmap b = Bitmap.createBitmap(1, 1, conf);
		int pxVal = ((0xff) << 24)
				  | ((0xff) << 16) //B
				  | ((0 & 0xff) << 8)  //G
				  | ((0xff));  //R
		b.setPixel(0, 0, pxVal);

        Texture tx = new Texture(b, numTextures);
        tx.name = "magenta";
        numTextures++;
        return tx;
    }
	
    public Texture sinGratingTexture(){
        int texWidth = 1500;
        int texHeight = 1;
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
        Bitmap b = Bitmap.createBitmap(texWidth, texHeight, conf); // this creates a MUTABLE bitmap
        for(int i = 0; i < texWidth; i++){
        	int val = (int) ((Math.sin( ((double) i) * 2 * Math.PI / texWidth )) * 127.5 + 127.5);
        	int pxVal = ((0xff) << 24)
        	        | ((val & 0xff) << 16)
        	        | ((val & 0xff) << 8)
        	        | ((val & 0xff));
        	b.setPixel(i, 0, pxVal);
        }

        Texture tx = new Texture(b, numTextures);
        tx.name = "sinGrating";
        numTextures++;
        return tx;
    }

    public Texture squareGratingTexture(){
        int texWidth = 1500;
        int texHeight = 1;
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
        Bitmap b = Bitmap.createBitmap(texWidth, texHeight, conf); // this creates a MUTABLE bitmap
        for(int i = 0; i < texWidth; i++){
        	int val = 0;
        	if(i >= texWidth / 2){
        		val = 255;
        	}
        	int pxVal = ((0xff) << 24)
        	        | ((val & 0xff) << 16)
        	        | ((val & 0xff) << 8)
        	        | ((val & 0xff));
        	    	b.setPixel(i, 0, pxVal);
        }

        Texture tx = new Texture(b, numTextures);
        tx.name = "sqrGrating";
        numTextures++;
        return tx;
    }

    // APERTURE TEXTURES
    public Texture circleTexture(){
    	double texWidth = 1501;
        double texHeight = texWidth;
        
        double texMiddleX = 750;
        double texMiddleY = texMiddleX;
        
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
        Bitmap b = Bitmap.createBitmap((int)texWidth, (int)texHeight, conf); // this creates a MUTABLE bitmap
        
        double circleLimit = Math.pow(texWidth/2, 2);

        double[] dxSquared = new double[(int)texWidth];
        for(int i = 0; i < texWidth; i++){
    		double dx = Math.abs(texMiddleX-i);
        	dxSquared[i] = Math.pow(dx,2);
        }
        
        for(int i = 0; i < texWidth; i++){
        	for(int j = 0; j < texHeight; j++){
        		int val = 0;
    			double d = dxSquared[i] + dxSquared[j]; 
        		if(d > circleLimit){
        			val = 255;
        		}
        		
	        	int pxVal = ((val  & 0xff) << 24)
	            | ((grayVal & 0xff) << 16)
	            | ((grayVal & 0xff) << 8)
	            | ((grayVal & 0xff));
	        	b.setPixel(i, j, pxVal);
        	}
        }

        Texture tx = new Texture(b, numTextures);
        tx.name = "circle";
        numTextures++;
        return tx;
    }
    
    public Texture gaborTexture(){
        double texWidth = 601;
        double texHeight = texWidth;
        
        double texMiddleX = 300;
        double texMiddleY = texMiddleX;
        
        //gauss params
        double sigma = 0.13; //decays nicely to -0.5 and +0.5
        double twoSigmaSquared = 2*Math.pow(sigma, 2);
        
        
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
        Bitmap b = Bitmap.createBitmap((int)texWidth, (int)texHeight, conf); // this creates a MUTABLE bitmap
        
        double[] dxSquared = new double[(int)texWidth];
        for(int i = 0; i < texWidth; i++){
        	dxSquared[i] = Math.pow((texMiddleX-i)/texWidth,2);
        }
        
        for(int i = 0; i < texWidth; i++){
        	for(int j = 0; j < texHeight; j++){
        		double xSquared = dxSquared[i] + dxSquared[j]; 
        		double valD = 255.0 - Math.round((Math.exp(-xSquared/twoSigmaSquared)) * 255.0);
	        	int val = (int) valD;
	        	
	        	//clamp -- may prevent weird precision artifacts
	        	if(val>255)
	        		val=255;
	        	if(val < 0)
	        		val = 0;
	        	
	        	int pxVal = ((val  & 0xff) << 24)
	            | ((grayVal & 0xff) << 16)
	            | ((grayVal & 0xff) << 8)
	            | ((grayVal & 0xff));
	        	b.setPixel(i, j, pxVal);
        	}
        }

        Texture tx = new Texture(b, numTextures);
        tx.name = "gabor";
        numTextures++;
        return tx;
    }

    public Texture squareTexture(){
    	//just a transparent aperture
        int texWidth = 1;
        int texHeight = 1;
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
        Bitmap b = Bitmap.createBitmap(texWidth, texHeight, conf); // this creates a MUTABLE bitmap
        for(int i = 0; i < texWidth; i++){
        	for(int j = 0; j < texHeight; j++){
	        	int pxVal = ((0 & 0xff) << 24)
	            | ((0xff) << 16)
	            | ((0xff) << 8)
	            | ((0xff));
	        	b.setPixel(i, 0, pxVal);
        	}
        }

        Texture tx = new Texture(b, numTextures);
        tx.name = "square";
        numTextures++;
        return tx;
    }

}
