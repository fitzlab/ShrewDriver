package com.example.stimbot;

import com.example.stimbot.MyRenderer;

import android.support.v7.app.ActionBarActivity;
import android.opengl.GLSurfaceView;
import android.os.Bundle;
import android.view.Menu;
import android.view.MotionEvent;
import android.view.View;

public class StimbotActivity extends ActionBarActivity {
	static View rootView;

	private GLSurfaceView mView;
	private MyRenderer mRenderer;
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
        mView = new GLSurfaceView(this);
        mRenderer = new MyRenderer(this);
        mView.setRenderer(mRenderer);
        setContentView(mView);
	}

	@Override
	public boolean onCreateOptionsMenu(Menu menu) {
        getActionBar().hide(); //obliterate the stupid title menu thing
        //hideCrap();
		return true;
	}
	
	public void hideCrap() {
		//gets rid of the menu bars at the top and bottom of the screen
		mView.setSystemUiVisibility(View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.INVISIBLE);
    }

    @Override
	public boolean onTouchEvent(MotionEvent event){
    	hideCrap();
    	return super.onTouchEvent(event);
    }



}
