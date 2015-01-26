package com.example.stimbot;

// Accepts serial commands and displays the stim on the screen accordingly
// Uses OpenGL ES 2.0. 
// The scene is an orthographic projection. 
// Far away is a "stim" object. This is a large square with a texture on it, e.g. a grating. 
// Closer to the camera is an "aperture" object, which is an alpha mask (e.g. a Gabor).

// Grating frequency and phase are controlled by manipulation of texture coordinates.
// Aperture position is changed by translation. When aperture moves, the stim object moves too,
// so that the phase of a grating won't change just because you moved the aperture.

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.nio.IntBuffer;
import java.nio.ShortBuffer;
import java.util.ArrayList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

import com.example.stimbot.Texture;

import android.content.Context;
import android.graphics.Bitmap;
import android.media.Ringtone;
import android.media.RingtoneManager;
import android.net.Uri;
import android.opengl.GLSurfaceView.Renderer;
import android.opengl.GLES20;
import android.os.PowerManager;
import android.os.PowerManager.WakeLock;
import android.util.Log;

class MyRenderer implements Renderer {
	private Context mContext;
	private StimbotActivity mActivity;
	
	private FloatBuffer mStimVertexBuffer = null;
	private FloatBuffer mStimColorBuffer = null;
	private ShortBuffer mStimTriangleIndexBuffer = null; 
	private FloatBuffer mStimTextureBuffer = null;
	private int mStimNumOfTriangleIndices = 0;
	
	private FloatBuffer mApertureVertexBuffer = null;
	private FloatBuffer mApertureColorBuffer = null;
	private ShortBuffer mApertureTriangleIndexBuffer = null; 
	private FloatBuffer mApertureTextureBuffer = null;
	private int mApertureNumOfTriangleIndices = 0;
	
	private int [] mTextureList = null;
	
	private float grayValf = 180f/255f;
	private TextureFactory textureFactory = new TextureFactory();

	private ArrayList<Texture> textures;
	
	SerialConnection serialConnection;
	
	private float stimPosZ = -2.0f;
	private float aperturePosZ = -1.0f;
	
	PowerManager pm;
	WakeLock mWakeLock;
	
	//--- Display state and serial variables ---//
	String serialDataBuffer = "";
	private String[] savedCommands = new String[100];

	private String stimTextureName = "sinGrating";
	private String apertureTextureName = "gabor";

	RenderedObject stim = new RenderedObject();
	RenderedObject aperture = new RenderedObject();
	
	public MyRenderer(StimbotActivity activity) {
		mActivity = activity;
		mContext = mActivity.getApplicationContext();
        serialConnection = new SerialConnection(activity);
        
        pm = (PowerManager) mContext.getSystemService(Context.POWER_SERVICE);
        mWakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK | PowerManager.ACQUIRE_CAUSES_WAKEUP, "tag");
		mWakeLock.acquire();
	}

    public void onSurfaceCreated(GL10 gl, EGLConfig config) {
    	gl.glClearColor(grayValf, grayValf, grayValf, 1.0f); //Equal luminant gray background
 		gl.glHint(GL10.GL_PERSPECTIVE_CORRECTION_HINT, GL10.GL_NICEST);
 		gl.glEnable(GL10.GL_DEPTH_TEST);
 		gl.glShadeModel(GL10.GL_SMOOTH);
 		gl.glEnable(GL10.GL_CULL_FACE);
    	gl.glCullFace(GL10.GL_BACK);
    	gl.glFrontFace(GL10.GL_CCW);
    	 
        gl.glEnableClientState(GL10.GL_VERTEX_ARRAY);
        gl.glEnableClientState(GL10.GL_COLOR_ARRAY);
        
        makeTextures(gl);
        
        // Get all the buffers ready
        makeStimObject();
        makeApertureObject();
	}
    
    public void onSurfaceChanged(GL10 gl, int width, int height) {
        gl.glViewport(0, 0, width, height);
        gl.glMatrixMode(GL10.GL_PROJECTION);
        gl.glLoadIdentity();
        
        //aspect ratio correction is now done in RenderedObject -- no need for it here.
        //float aspect = (float)nexusScreenWidthPx / nexusScreenHeightPx;
        float aspect = 1.0f;
        gl.glOrthof(-aspect, aspect, -1.0f, 1.0f, 1.0f, 1000.0f);
   }
    
    public void onDrawFrame(GL10 gl) {
        gl.glClear(GL10.GL_COLOR_BUFFER_BIT | GL10.GL_DEPTH_BUFFER_BIT);
        gl.glMatrixMode(GL10.GL_MODELVIEW);

        gl.glEnable(GL10.GL_BLEND);
        gl.glBlendFunc(GL10.GL_SRC_ALPHA, GL10.GL_ONE_MINUS_SRC_ALPHA);

        stim.computeParams();
        aperture.computeParams();
        
        drawStim(gl);
        drawAperture(gl);
       
        // Done drawing! Let's see if we have any new commands waiting in the serial.
        checkSerial(); 
    }

    private void drawStim(GL10 gl){
    	//translate stim to its position and make it the right size
        gl.glMatrixMode(GL10.GL_MODELVIEW);
        gl.glLoadIdentity();
        gl.glTranslatef(stim.posX, stim.posY, stim.posZ);
        gl.glScalef(stim.scaleX, stim.scaleY, stim.scaleZ);
        gl.glRotatef(stim.angleX, 1, 0, 0);
		gl.glRotatef(stim.angleY, 0, 1, 0);
		gl.glRotatef(stim.angleZ, 0, 0, 1);

		//put the current stim texture on it
        applyStimTexture(gl);
        
        //adjust texture position as needed.
        //Note that we apply translation FIRST here, so that phase will act the same at all rotations + scales.
        gl.glMatrixMode(GL10.GL_TEXTURE);
        gl.glLoadIdentity();
        gl.glTranslatef(stim.texturePosX, stim.texturePosY, stim.texturePosZ); //texture position: phase and animation
        gl.glRotatef(stim.textureAngleX, 1, 0, 0); //texture rotation gives grating orientation
		gl.glRotatef(stim.textureAngleY, 0, 1, 0);
		gl.glRotatef(stim.textureAngleZ, 0, 0, 1);
        gl.glScalef(stim.textureScaleX, stim.textureScaleY, stim.textureScaleZ); //texture scaling: spatial frequency
        gl.glTranslatef(-0.5f, -0.5f, stim.texturePosZ);
        
		// Draw stim object
        gl.glVertexPointer(3, GL10.GL_FLOAT, 0, mStimVertexBuffer);
        gl.glColorPointer(4, GL10.GL_FLOAT, 0, mStimColorBuffer);
        gl.glTexCoordPointer(2, GL10.GL_FLOAT, 0, mStimTextureBuffer);
        gl.glDrawElements(GL10.GL_TRIANGLES, mStimNumOfTriangleIndices,
    			GL10.GL_UNSIGNED_SHORT, mStimTriangleIndexBuffer);
    }
    
    private void drawAperture(GL10 gl){
    	//we do what we must, because we can
        gl.glMatrixMode(GL10.GL_MODELVIEW);
        gl.glLoadIdentity();
        gl.glTranslatef(aperture.posX, aperture.posY, aperture.posZ);
        gl.glScalef(aperture.scaleX, aperture.scaleY, aperture.scaleZ);
        gl.glRotatef(aperture.angleX, 1, 0, 0);
		gl.glRotatef(aperture.angleY, 0, 1, 0);
		gl.glRotatef(aperture.angleZ, 0, 0, 1);
        
        applyApertureTexture(gl);
        
        //Make sure no transform is applied to the aperture texture
        gl.glMatrixMode(GL10.GL_TEXTURE);
        gl.glLoadIdentity();
        
        // Draw aperture object
        gl.glVertexPointer(3, GL10.GL_FLOAT, 0, mApertureVertexBuffer);
        gl.glColorPointer(4, GL10.GL_FLOAT, 0, mApertureColorBuffer);
        gl.glTexCoordPointer(2, GL10.GL_FLOAT, 0, mApertureTextureBuffer);
        gl.glDrawElements(GL10.GL_TRIANGLES, mApertureNumOfTriangleIndices,
    			GL10.GL_UNSIGNED_SHORT, mApertureTriangleIndexBuffer);
    }
    
	public void makeTextures(GL10 gl){
		//stim textures
		textures = new ArrayList<Texture>();
		
		//gratings
		textures.add(textureFactory.squareGratingTexture());
		textures.add(textureFactory.sinGratingTexture());
		
		//color patches
		textures.add(textureFactory.whiteTexture());
		textures.add(textureFactory.grayTexture());
		textures.add(textureFactory.blackTexture());
		textures.add(textureFactory.redTexture());
		textures.add(textureFactory.blueTexture());
		textures.add(textureFactory.greenTexture());
		textures.add(textureFactory.cyanTexture());
		textures.add(textureFactory.magentaTexture());
		textures.add(textureFactory.yellowTexture());

		//apertures
		textures.add(textureFactory.gaborTexture());
		textures.add(textureFactory.squareTexture());
		textures.add(textureFactory.circleTexture());
		
		mTextureList = new int[textureFactory.numTextures];
		
		gl.glEnable(GL10.GL_TEXTURE_2D);
		gl.glGenTextures(textureFactory.numTextures, mTextureList, 0);
		
		for(int i = 0; i < textures.size(); i++){	
			gl.glBindTexture(GL10.GL_TEXTURE_2D, mTextureList[i]);
			gl.glTexParameterf(GL10.GL_TEXTURE_2D, GL10.GL_TEXTURE_WRAP_S, GL10.GL_REPEAT);
			gl.glTexParameterf(GL10.GL_TEXTURE_2D, GL10.GL_TEXTURE_WRAP_S, GL10.GL_REPEAT);
			gl.glTexParameterf(GL10.GL_TEXTURE_2D, GL10.GL_TEXTURE_MAG_FILTER, GL10.GL_LINEAR);
			gl.glTexParameterf(GL10.GL_TEXTURE_2D, GL10.GL_TEXTURE_MIN_FILTER, GL10.GL_LINEAR);
			gl.glTexEnvf(GL10.GL_TEXTURE_ENV, GL10.GL_TEXTURE_ENV_MODE, GL10.GL_MODULATE);
			gl.glClientActiveTexture(GL10.GL_TEXTURE0);
			gl.glEnableClientState(GL10.GL_TEXTURE_COORD_ARRAY);
			
			Bitmap bmp = textures.get(i).bitmap;
			if(textures.get(i).index != i){
				Log.e("ERROR", "Wrong index on texture -- did you make these in the right order?");
			}
			
			int width = bmp.getWidth();
			int height = bmp.getHeight();
			int bufPos = 0;
			int[] data = new int[bmp.getWidth()*bmp.getHeight()];
			for(int x = 0; x < bmp.getWidth(); x++){
				for(int y = 0; y < bmp.getHeight(); y++){
					data[bufPos] = bmp.getPixel(x, y);
					bufPos++;
				}
			}
			IntBuffer b = IntBuffer.wrap(data);
			
        	//GLUtils.texImage2D(GL10.GL_TEXTURE_2D, 0, GL10.GL_RGBA, bmp, 0); //using this produces some nasty artifacts at low alpha, idk why
        	gl.glTexImage2D(GL10.GL_TEXTURE_2D, 0, GL10.GL_RGBA, width, height, 0, GL10.GL_RGBA, GL10.GL_UNSIGNED_BYTE, b);
		}
		
	}

    private void applyStimTexture(GL10 gl){
    	for(int i = 0; i < textures.size(); i++){
    		if(textures.get(i).name.equalsIgnoreCase(stimTextureName)){
            	gl.glBindTexture(GL10.GL_TEXTURE_2D, mTextureList[textures.get(i).index]);
            	return;
    		}
    	}
		Log.d("stim","no tex found");
    }
    
    private void applyApertureTexture(GL10 gl){
    	for(int i = 0; i < textures.size(); i++){
    		if(textures.get(i).name.equalsIgnoreCase(apertureTextureName)){
            	gl.glBindTexture(GL10.GL_TEXTURE_2D, mTextureList[textures.get(i).index]);
            	return;
    		}
    	}
		Log.d("aperture","no tex found");
    }
    
    public void checkSerial(){
         try{
 			serialDataBuffer += serialConnection.checkSerial();
 		}
 		catch(Exception ex){
 			arduinoError(ex);
 		}
 		
 		//parse serial data for commands
 		int newlinePos = serialDataBuffer.indexOf('\n');
 		if(newlinePos != -1){
 			String cmdString = serialDataBuffer.substring(0, newlinePos);
 			//keep the remainder of the buffer, if there's anything there
 			if(serialDataBuffer.length() > newlinePos+1){
 				serialDataBuffer = serialDataBuffer.substring(newlinePos+1, serialDataBuffer.length());
 			}
 			else{
 				serialDataBuffer = "";
 			}
 			
 			//find each token in the command string
 			String[] tokens = cmdString.split(" ");
 			
 			for(int t = 0; t < tokens.length; t++){
 				//each token consists of a command and (often) a number. Split it up into those pieces.
 				String cmd = "";
 				Float number = null;
 				
 				Pattern p = Pattern.compile("[a-z|A-Z]+");
 				Matcher m = p.matcher(tokens[t]);
 				int numberPos = -1;
 				if(m.find()){
 					numberPos = m.end();
 					cmd = tokens[t].substring(0, m.end());
 					//Log.d("Serial", "Entered command: (" + cmd + ")");
 					if(numberPos < tokens[t].length()){
 						
 						String numberStr = tokens[t].substring(numberPos,tokens[t].length());
 						try{
 							number = Float.parseFloat(numberStr);
 						}
 						catch(Exception ex){
 							Log.d("Serial", "Error parsing command string: (" + cmdString + ") at token (" + tokens[t] + ")");
 						}
 					}
 				}
 				else if(! tokens[t].trim().isEmpty()){
 					//it may be just a number, invoking a saved command
 					cmd = "";
 					try{
 						number = Float.parseFloat(tokens[t]);
 					}
 					catch(Exception ex){
 						Log.d("Serial", "Error parsing command string: (" + cmdString + ") at token (" + tokens[t] + ")");
 					}
 				}
 				else{
 					//no command here, probably just a stray blank space
 					continue;
 				}
 				
 				/* --- SYSTEM COMMANDS --- */
 				
 				if(cmd.equalsIgnoreCase("screenon")){
 					//make some noise
 			        Uri notification = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
 	    			Ringtone r = RingtoneManager.getRingtone(mContext, notification);
 			        r.play();
 	
 			        //engage wake lock, forcing screen to turn on
 					if(!mWakeLock.isHeld()){
 						mWakeLock.acquire();
 					}
 				}
 				
 				if(cmd.equalsIgnoreCase("screenoff")){
 					//make some noise
 					Uri notification = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
 	    			Ringtone r = RingtoneManager.getRingtone(mContext, notification);
 			        r.play();
 	
 			        //Release wake lock, allowing screen to turn off naturally 
 					if(mWakeLock.isHeld()){
 						mWakeLock.release();
 					}
 				}
 				
 				if(cmd.equalsIgnoreCase("blonk")){
 					//make noise, confirm serial connection works
 			        Uri notification = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
 	    			Ringtone r = RingtoneManager.getRingtone(mContext, notification);
 			        r.play();
 				}

 				/* --- STIM COMMANDS --- */
 				
 				if(cmd.equalsIgnoreCase("screendist") && number != null){
 					stim.setScreenDistanceMillis(number);
 					aperture.setScreenDistanceMillis(number);
 				}
 				
 				if(cmd.equalsIgnoreCase("sin") && number != null){
 					//display sinusoidal grating at given orientation
 					//change to lab's bizarre coordinate system standard
 					stimTextureName = "sinGrating";
 					stim.gratingOrientation = number;
 				}
 			
 				if(cmd.equalsIgnoreCase("sqr") && number != null){
 					//display square wave grating at given orientation
 					stimTextureName = "sqrGrating";
 					stim.gratingOrientation = number;
 				}
 				
 				//colors
 				if(cmd.equalsIgnoreCase("pag")){
 					stimTextureName = "gray";
 				}
 				if(cmd.equalsIgnoreCase("pab")){
 					stimTextureName = "black";
 				}
 				if(cmd.equalsIgnoreCase("paw")){
 					stimTextureName = "white";
 				}
 				if(cmd.equalsIgnoreCase("par")){
 					stimTextureName = "red";
 				}
 				if(cmd.equalsIgnoreCase("pae")){
 					stimTextureName = "green";
 				}
 				if(cmd.equalsIgnoreCase("pau")){
 					stimTextureName = "blue";
 				}
 				if(cmd.equalsIgnoreCase("pac")){
 					stimTextureName = "cyan";
 				}
 				if(cmd.equalsIgnoreCase("pay")){
 					stimTextureName = "yellow";
 				}
 				if(cmd.equalsIgnoreCase("pam")){
 					stimTextureName = "magenta";
 				}

 				if(cmd.equalsIgnoreCase("px") && number != null){
 					stim.centerXDegrees = number;
 					aperture.centerXDegrees = number;
 				}
 				
 				if(cmd.equalsIgnoreCase("py") && number != null){
 					stim.centerYDegrees = number;
 					aperture.centerYDegrees = number;
 				}
 				
 				if(cmd.equalsIgnoreCase("sx") && number != null){
 					stim.sizeXDegrees = number;
 					aperture.sizeXDegrees = number;
 				}
 				
 				if(cmd.equalsIgnoreCase("sy") && number != null){
 					stim.sizeYDegrees = number;
 					aperture.sizeYDegrees = number;
 				}
 				
 				if(cmd.equalsIgnoreCase("ac")){
 					apertureTextureName = "circle";
 				}
 				
 				if(cmd.equalsIgnoreCase("ag")){
 					apertureTextureName = "gabor";
 				}

 				if(cmd.equalsIgnoreCase("af")){
 					apertureTextureName = "fullScreen";
 				}
 				
 				if(cmd.equalsIgnoreCase("as")){
 					apertureTextureName = "square";
 				}

 				/* --- GRATING-SPECFIC COMMANDS --- */

 				if(cmd.equalsIgnoreCase("sf") && number != null){
 					stim.spatialFrequency = number;
 				}
 				
 				if(cmd.equalsIgnoreCase("tf") && number != null){
 					stim.temporalFrequency = number;
 				}

 				if(cmd.equalsIgnoreCase("jf")){
 					stim.jitterFrequency = number;
 				}

 				if(cmd.equalsIgnoreCase("ja")){
 					stim.jitterAmount = number;
 				}
 				
 				if(cmd.equalsIgnoreCase("ph")){
 					stim.setPhase(number);
 				}

 				/* --- SAVED COMMANDS --- */
 				if(cmd.equalsIgnoreCase("save") && number != null){
 					int idx = (int) number.floatValue();
 					if(idx > 99 || idx < 0){
 						continue;
 					}
 					savedCommands[idx] = "";
 					//add the remainder of this string to the command
 					for(int u = t+1; u < tokens.length; u++){
 						if(!tokens[u].startsWith("save")){ //don't want users to start saving save commands, could get messy
 							savedCommands[idx] += tokens[u] + " ";
 						}
 					}
 					savedCommands[idx] += "\n";
 					t = tokens.length;
 				}
 				
 				if(cmd.isEmpty() && number != null){
 					int idx = (int) number.floatValue();
 					if(idx > 99 || idx < 0){
 						continue;
 					}
 					//Log.d("Serial", "loaded command " + idx + " (" + savedCommands[idx] + ")");
 					serialDataBuffer = savedCommands[idx] + serialDataBuffer;
 					checkSerial();
 				}
 			}
 		}
     }

 	public void arduinoError(Exception ex){
 		//Log.d("Error", "Can't connect to Arduino: " + ex.toString());
 	}
 	
     
     private void makeStimObject(){
     	// Set vertex buffer
     	float squareSize = 1.0f;
         float vertexlist[] = {
                 -squareSize,  squareSize, stimPosZ,   // top left
                 -squareSize, -squareSize, stimPosZ,   // bottom left
                  squareSize, -squareSize, stimPosZ,   // bottom right
                  squareSize,  squareSize, stimPosZ}; // top right
     	ByteBuffer vbb = ByteBuffer.allocateDirect(vertexlist.length * 4);
 		vbb.order(ByteOrder.nativeOrder());
 		mStimVertexBuffer = vbb.asFloatBuffer();
 		mStimVertexBuffer.put(vertexlist);
 		mStimVertexBuffer.position(0);
 		
 		// Set triangle buffer with vertex indices
 		short trigindexlist[] = { 0, 1, 2, 0, 2, 3 };
 		
 		mStimNumOfTriangleIndices = trigindexlist.length;
 		ByteBuffer ibb = ByteBuffer.allocateDirect(trigindexlist.length * 2);
 		ibb.order(ByteOrder.nativeOrder());
 		mStimTriangleIndexBuffer = ibb.asShortBuffer();
 		mStimTriangleIndexBuffer.put(trigindexlist);
 		mStimTriangleIndexBuffer.position(0);
 		
 		// Set triangle color buffer
 		float trigcolorlist[] = { 
 				1.0f, 1.0f, 1.0f, 1.0f,
 				1.0f, 1.0f, 1.0f, 1.0f,
 				1.0f, 1.0f, 1.0f, 1.0f,
 				1.0f, 1.0f, 1.0f, 1.0f
 		};
 		
 		ByteBuffer cbb = ByteBuffer.allocateDirect(trigcolorlist.length * 4);
 		cbb.order(ByteOrder.nativeOrder());
 		mStimColorBuffer = cbb.asFloatBuffer();
 		mStimColorBuffer.put(trigcolorlist);
 		mStimColorBuffer.position(0);
 		
 		// Set texture buffer
 		float texturecoords[] = {0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 1.0f, 1.0f, 0.0f}; 
 		
 		ByteBuffer tbb = ByteBuffer.allocateDirect(texturecoords.length * 4);
 		tbb.order(ByteOrder.nativeOrder());
 		mStimTextureBuffer = tbb.asFloatBuffer();
 		mStimTextureBuffer.put(texturecoords);
 		mStimTextureBuffer.position(0);
     }
     
     private void makeApertureObject(){
     	// Set vertex buffer
     	float squareSize = 1.0f;
         float vertexlist[] = {
                 -squareSize,  squareSize, aperturePosZ,   // top left
                 -squareSize, -squareSize, aperturePosZ,   // bottom left
                  squareSize, -squareSize, aperturePosZ,   // bottom right
                  squareSize,  squareSize, aperturePosZ }; // top right
     	ByteBuffer vbb = ByteBuffer.allocateDirect(vertexlist.length * 4);
 		vbb.order(ByteOrder.nativeOrder());
 		mApertureVertexBuffer = vbb.asFloatBuffer();
 		mApertureVertexBuffer.put(vertexlist);
 		mApertureVertexBuffer.position(0);
 		
 		// Set triangle buffer with vertex indices
 		short trigindexlist[] = { 0, 1, 2, 0, 2, 3 };
 		
 		mApertureNumOfTriangleIndices = trigindexlist.length;
 		ByteBuffer ibb = ByteBuffer.allocateDirect(trigindexlist.length * 2);
 		ibb.order(ByteOrder.nativeOrder());
 		mApertureTriangleIndexBuffer = ibb.asShortBuffer();
 		mApertureTriangleIndexBuffer.put(trigindexlist);
 		mApertureTriangleIndexBuffer.position(0);
 		
 		// Set triangle color buffer
 		float trigcolorlist[] = { 
 				//r,g,b,a
 				1.0f, 1.0f, 1.0f, 1.0f,    
 				1.0f, 1.0f, 1.0f, 1.0f,    
 				1.0f, 1.0f, 1.0f, 1.0f,    
 				1.0f, 1.0f, 1.0f, 1.0f
 		};
 		
 		ByteBuffer cbb = ByteBuffer.allocateDirect(trigcolorlist.length * 4);
 		cbb.order(ByteOrder.nativeOrder());
 		mApertureColorBuffer = cbb.asFloatBuffer();
 		mApertureColorBuffer.put(trigcolorlist);
 		mApertureColorBuffer.position(0);
 		
 		// Set texture buffer
 		float texturecoords[] = {0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 1.0f, 1.0f, 0.0f}; 
 		
 		ByteBuffer tbb = ByteBuffer.allocateDirect(texturecoords.length * 4);
 		tbb.order(ByteOrder.nativeOrder());
 		mApertureTextureBuffer = tbb.asFloatBuffer();
 		mApertureTextureBuffer.put(texturecoords);
 		mApertureTextureBuffer.position(0);
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
