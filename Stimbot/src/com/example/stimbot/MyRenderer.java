package com.example.stimbot;

/*
 * MyRenderer (Example 3)
 * 
 * [AUTHOR]: Chunyen Liu
 * [SDK   ]: Android SDK 2.1 and up
 * [NOTE  ]: developer.com tutorial, "Fundamental OpenGL ES in Android"
 */

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.nio.ShortBuffer;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.media.Ringtone;
import android.media.RingtoneManager;
import android.net.Uri;
import android.opengl.GLSurfaceView.Renderer;
import android.opengl.GLES20;
import android.opengl.GLUtils;
import android.opengl.Matrix;
import android.util.Log;
import android.view.MotionEvent;

class MyRenderer implements Renderer {
	private Context mContext;
	private FloatBuffer mVertexBuffer = null;
	private FloatBuffer mColorBuffer = null;
	private ShortBuffer mTriangleIndexBuffer = null; 
	private int mNumOfTriangleIndices = 0;
	private FloatBuffer mTextureBuffer = null;
	private int [] mTextureList = null;

	private Bitmap txGrating;
	private Bitmap txBlack;
	private Bitmap txGray;

	private int txBlackIndex = -1;
	private int txGrayIndex = -1;
	private int txGratingIndex = -1;
	
	public float mAngleX = 0.0f;
	public float mAngleY = 0.0f;
	public float mAngleZ = 0.0f;
	private final float TOUCH_SCALE_FACTOR = 0.6f;
    

	SerialConnection serialConnection;
	String serialDataBuffer = "";
	
	public MyRenderer(Context context) {
		mContext = context;
        serialConnection = new SerialConnection((Activity) context);
	}
	
    public void onDrawFrame(GL10 gl) {
        gl.glClear(GL10.GL_COLOR_BUFFER_BIT | GL10.GL_DEPTH_BUFFER_BIT);
        gl.glMatrixMode(GL10.GL_MODELVIEW);
        gl.glLoadIdentity();
        
        gl.glTranslatef(0, 0, -3.0f);
        gl.glRotatef(mAngleX, 1, 0, 0);
		gl.glRotatef(mAngleY, 0, 1, 0);
		gl.glRotatef(mAngleZ, 0, 0, 1);
        
		// Draw all textured triangles
        gl.glVertexPointer(3, GL10.GL_FLOAT, 0, mVertexBuffer);
        gl.glColorPointer(4, GL10.GL_FLOAT, 0, mColorBuffer);
        
        gl.glTexCoordPointer(2, GL10.GL_FLOAT, 0, mTextureBuffer);
        gl.glDrawElements(GL10.GL_TRIANGLES, mNumOfTriangleIndices,
    			GL10.GL_UNSIGNED_SHORT, mTriangleIndexBuffer);
        
        
        try{
			serialDataBuffer += serialConnection.checkSerial();
		}
		catch(Exception ex){
			arduinoError(ex);
		}
			
		//parse serial data for commands
		int newlinePos = serialDataBuffer.indexOf('\n');
		if(newlinePos != -1){
			String cmd = serialDataBuffer.substring(0, newlinePos);
			//keep the remainder of the buffer, if there's anything there
			if(serialDataBuffer.length() > newlinePos+1){
				serialDataBuffer = serialDataBuffer.substring(newlinePos+1, serialDataBuffer.length());
			}
			else{
				serialDataBuffer = "";
			}
			
			if(cmd.equalsIgnoreCase("blonk")){
				//make noise, confirm serial connection works

		        Uri notification = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
    			Ringtone r = RingtoneManager.getRingtone(mContext, notification);
		        r.play();
			}

			if(cmd.startsWith("o")){
				//display grating at given orientation
				try{
					mAngleZ = Float.parseFloat(cmd.substring(1,cmd.length()));
					mAngleZ = 90 - mAngleZ; //change to lab's bizarre coordinate system standard
					setTextureToGrating(gl);
				}
				catch(Exception ex){
					//malformed command, do nothing
				}
			}

			if(cmd.equals("g")){
				//show gray screen
	        	setTextureToGray(gl);
			}

			if(cmd.equals("b")){
				//black screen
	        	setTextureToBlack(gl);
			}
		}
    }

	public void arduinoError(Exception ex){
		Log.d("Error", "Can't connect to Arduino: " + ex.toString());
	}
	
    public void onSurfaceCreated(GL10 gl, EGLConfig config) {
    	gl.glClearColor(0.0f, 0.0f, 0.0f, 0.0f);
 		gl.glHint(GL10.GL_PERSPECTIVE_CORRECTION_HINT, GL10.GL_NICEST);
 		gl.glEnable(GL10.GL_DEPTH_TEST);
 		gl.glShadeModel(GL10.GL_SMOOTH);
 		gl.glEnable(GL10.GL_CULL_FACE);
    	gl.glCullFace(GL10.GL_BACK);
    	gl.glFrontFace(GL10.GL_CCW);
    	 
        gl.glEnableClientState(GL10.GL_VERTEX_ARRAY);
        gl.glEnableClientState(GL10.GL_COLOR_ARRAY);
        
        makeTextures(gl);
        setTextureToBlack(gl);
        
        // Get all the buffers ready
        setAllBuffers();
	}

    public void makeTextures(GL10 gl){
    	//make grating
    	txGrating = makeSquareTexture();
    	
    	//make black and gray textures
    	Bitmap.Config conf = Bitmap.Config.ARGB_8888; //4 bytes, alpha-red-green-blue
    	
    	txBlack = Bitmap.createBitmap(1, 1, conf);
    	int blackVal = 0;
    	txBlack.setPixel(0, 0, blackVal);
    	
    	txGray = Bitmap.createBitmap(1, 1, conf);
    	int grayVal = 180; //This is an equal-luminant gray (or very close -- double check with a photodiode later.)
    	int pxVal = ((grayVal  & 0xff) << 24)
    	        | ((0xff) << 16)
    	        | ((0xff) << 8)
    	        | ((0xff));
    	txGray.setPixel(0, 0, pxVal);
    	
    	
        gl.glEnable(GL10.GL_TEXTURE_2D);
        
        int numTextures = 3;
		mTextureList = new int[numTextures];
        gl.glGenTextures(numTextures, mTextureList, 0);
        
	    for(int i = 0; i < numTextures; i++){   
			gl.glBindTexture(GL10.GL_TEXTURE_2D, mTextureList[i]);
			gl.glTexParameterf(GL10.GL_TEXTURE_2D, GL10.GL_TEXTURE_WRAP_S, GL10.GL_REPEAT);
			gl.glTexParameterf(GL10.GL_TEXTURE_2D, GL10.GL_TEXTURE_WRAP_S, GL10.GL_REPEAT);
			gl.glTexParameterf(GL10.GL_TEXTURE_2D, GL10.GL_TEXTURE_MAG_FILTER, GL10.GL_LINEAR);
			gl.glTexParameterf(GL10.GL_TEXTURE_2D, GL10.GL_TEXTURE_MIN_FILTER, GL10.GL_LINEAR);
			gl.glTexEnvf(GL10.GL_TEXTURE_ENV, GL10.GL_TEXTURE_ENV_MODE, GL10.GL_MODULATE);
			gl.glClientActiveTexture(GL10.GL_TEXTURE0);
	        gl.glEnableClientState(GL10.GL_TEXTURE_COORD_ARRAY);
	        
	        if(i==0){
	        	GLUtils.texImage2D(GL10.GL_TEXTURE_2D, 0, txBlack, 0);
	        	txBlackIndex = i;
	        }
	        if(i==1){
	        	GLUtils.texImage2D(GL10.GL_TEXTURE_2D, 0, txGray, 0);
	        	txGrayIndex = i; 
	    	}
	        if(i==2){
	        	GLUtils.texImage2D(GL10.GL_TEXTURE_2D, 0, txGrating, 0);
	        	txGratingIndex = i;
    		}
	    }
	    
    }

    public void setTextureToBlack(GL10 gl){
    	if(txBlackIndex >= 0){
    		gl.glBindTexture(GL10.GL_TEXTURE_2D, mTextureList[txBlackIndex]);
    	}
    	serialConnection.writeSerialLine("b");
    }
    public void setTextureToGray(GL10 gl){
    	if(txGrayIndex >= 0){
        	gl.glBindTexture(GL10.GL_TEXTURE_2D, mTextureList[txGrayIndex]);
    	}
    	serialConnection.writeSerialLine("g");
    }
    public void setTextureToGrating(GL10 gl){
    	if(txGratingIndex >= 0){
        	gl.glBindTexture(GL10.GL_TEXTURE_2D, mTextureList[txGratingIndex]);
    	}
    	serialConnection.writeSerialLine("G");
    }

    private Bitmap makeSinTexture(){
        int texWidth = 1500;
        int texHeight = 1;
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
        Bitmap b = Bitmap.createBitmap(texWidth, texHeight, conf); // this creates a MUTABLE bitmap
        for(int i = 0; i < texWidth; i++){
        	int val = (int) ((Math.sin( ((double) i) * 2 * Math.PI / texWidth )) * 127.5 + 127.5);
        	int pxVal = ((val  & 0xff) << 24)
            | ((0xff) << 16)
            | ((0xff) << 8)
            | ((0xff));
        	b.setPixel(i, 0, pxVal);
        }
        return b;
    }

    private Bitmap makeSquareTexture(){
        int texWidth = 1500;
        int texHeight = 1;
        Bitmap.Config conf = Bitmap.Config.ARGB_8888; // see other conf types
        Bitmap b = Bitmap.createBitmap(texWidth, texHeight, conf); // this creates a MUTABLE bitmap
        for(int i = 0; i < texWidth; i++){
        	int val = 0;
        	if(i >= texWidth / 2){
        		val = 255;
        	}
        	int pxVal = ((val  & 0xff) << 24)
            | ((0xff) << 16)
            | ((0xff) << 8)
            | ((0xff));
        	b.setPixel(i, 0, pxVal);
        }
        return b;
    }
    
    public void onSurfaceChanged(GL10 gl, int width, int height) {
        gl.glViewport(0, 0, width, height);
        float aspect = (float)width / height;
        gl.glMatrixMode(GL10.GL_PROJECTION);
        gl.glLoadIdentity();
        gl.glFrustumf(-aspect, aspect, -1.0f, 1.0f, 1.0f, 10.0f);
        
   }
    
    private void setAllBuffers(){
    	// Set vertex buffer
        float vertexlist[] = {
                -12.0f,  12.0f, 0.0f,   // top left
                -12.0f, -12.0f, 0.0f,   // bottom left
                 12.0f, -12.0f, 0.0f,   // bottom right
                 12.0f,  12.0f, 0.0f }; // top right
    	ByteBuffer vbb = ByteBuffer.allocateDirect(vertexlist.length * 4);
		vbb.order(ByteOrder.nativeOrder());
		mVertexBuffer = vbb.asFloatBuffer();
		mVertexBuffer.put(vertexlist);
		mVertexBuffer.position(0);
		
		// Set triangle buffer with vertex indices
		short trigindexlist[] = { 0, 1, 2, 0, 2, 3 };
		
		mNumOfTriangleIndices = trigindexlist.length;
		ByteBuffer ibb = ByteBuffer.allocateDirect(trigindexlist.length * 2);
		ibb.order(ByteOrder.nativeOrder());
		mTriangleIndexBuffer = ibb.asShortBuffer();
		mTriangleIndexBuffer.put(trigindexlist);
		mTriangleIndexBuffer.position(0);
		
		// Set triangle color buffer 
		float trigcolorlist[] = { 
				1.0f, 1.0f, 1.0f, 1.0f,    
				1.0f, 1.0f, 1.0f, 1.0f,    
				1.0f, 1.0f, 1.0f, 1.0f,    
				1.0f, 1.0f, 1.0f, 1.0f
		};
		
		ByteBuffer cbb = ByteBuffer.allocateDirect(trigcolorlist.length * 4);
		cbb.order(ByteOrder.nativeOrder());
		mColorBuffer = cbb.asFloatBuffer();
		mColorBuffer.put(trigcolorlist);
		mColorBuffer.position(0);
		
		// Set texture buffer
		float gratingFrequency = 10.0f; /// <--- Right now this is how to control spatial frequency.
		float texturecoords[] = {0.0f, 0.0f,   0.0f, gratingFrequency,   gratingFrequency, gratingFrequency,   gratingFrequency, 0.0f}; 
		
		ByteBuffer tbb = ByteBuffer.allocateDirect(texturecoords.length * 4);
		tbb.order(ByteOrder.nativeOrder());
		mTextureBuffer = tbb.asFloatBuffer();
		mTextureBuffer.put(texturecoords);
		mTextureBuffer.position(0);
    }
    
    /**
     * Utility method for compiling a OpenGL shader.
     *
     * <p><strong>Note:</strong> When developing shaders, use the checkGlError()
     * method to debug shader coding errors.</p>
     *
     * @param type - Vertex or fragment shader type.
     * @param shaderCode - String containing the shader code.
     * @return - Returns an id for the shader.
     */
    public static int loadShader(int type, String shaderCode){

        // create a vertex shader type (GLES20.GL_VERTEX_SHADER)
        // or a fragment shader type (GLES20.GL_FRAGMENT_SHADER)
        int shader = GLES20.glCreateShader(type);

        // add the source code to the shader and compile it
        GLES20.glShaderSource(shader, shaderCode);
        GLES20.glCompileShader(shader);

        return shader;
    }
}
