package com.example.stimbot;

import java.io.IOException;

import android.app.Activity;
import android.content.Context;
import android.hardware.usb.UsbManager;
import android.media.Ringtone;
import android.media.RingtoneManager;
import android.net.Uri;
import android.util.Log;

import com.hoho.android.usbserial.driver.UsbSerialDriver;
import com.hoho.android.usbserial.driver.UsbSerialProber;

public class SerialConnection{

    public static final boolean LOW   = false;
    public static final boolean HIGH  = true;

    private UsbSerialDriver usb;
    private Activity context;
    
    public SerialConnection(Activity context){
        this.context = context;
        UsbManager manager = (UsbManager) context.getSystemService(Context.USB_SERVICE);
        this.usb = UsbSerialProber.acquire(manager);
        
        connect();
    }
    
    public void connect(){
        try{
            if(this.usb == null) throw new IOException("device not found");
            this.usb.open();
            this.usb.setBaudRate(57600);
            
            //play a tone to confirm connection success
			Uri notification = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
			Ringtone r = RingtoneManager.getRingtone(context, notification);
			r.play();
			
            Thread.sleep(3000); //wait for Arduino to wake up after connecting
        }
        catch(Exception ex){
            Log.d("Exception in connect()", ex.toString());
        }
    }
    
    public String checkSerial(){
        String serialInput = "";
        try{
	    	byte buf[] = new byte[4096];
	        int size = usb.read(buf, 100);
        	for(int i = 0; i < size; i++){
        		serialInput += (char)buf[i];
            }
        }
        catch(IOException e){
            close();
        }
        return serialInput;//returnString;
    }
    
    public void writeSerialLine(String s){
    	s+="\n";
    	try{
    		byte buf[] = new byte[(s.length())];
    		for(int i = 0; i < s.length(); i++){
    			buf[i] = (byte) s.charAt(i);
            }
    		usb.write(buf, 100);
    	}
    	catch(Exception e){
            Log.d("omg","ohnoes");
        }
    }
    
    public boolean isOpen(){
        return this.usb != null;
    }

    public boolean close(){
        try{
            this.usb.close();
            this.usb = null;
            return true;
        }
        catch(IOException e){
            return false;
        }
    }

    public void write(byte[] writeData){
        try{
            if(this.isOpen()) this.usb.write(writeData, 100);
        }
        catch(IOException e){
            this.close();
        }
    }

    public void write(byte writeData){
        byte[] _writeData = {(byte)writeData};
        write(_writeData);
    }
    
    public void startReadThread(){
    	// Unused.
        // Leaving this here as an example of how to do serial reads in a separate thread.
        // For our purposes, though, we can comfortably check for serial updates between frames. 
        /*
        //start read thread
        if(this.th_receive == null){ 
            this.th_receive = new Thread(new Runnable(){
            		//read thread behavior
                    public void run(){
                        while(isOpen()){
                            try{
                                byte buf[] = new byte[4096];
                                int size = usb.read(buf, 100);
                                if(size > 0){
                                    for(int i = 0; i < size; i++){
                                        processInput(buf[i]);
                                    }
                                }
                                Thread.sleep(5); //<--- potential latency issue here! Test with shorter pauses or call between frame updates.
                            }
                            catch(IOException e){
                                close();
                                if(handler!=null) handler.onClose();
                            }
                            catch(InterruptedException e){
                                if(handler!=null) handler.onError(e.toString());
                            }
                        }
                    }
                });
            this.th_receive.start();
        }*/
    }
}