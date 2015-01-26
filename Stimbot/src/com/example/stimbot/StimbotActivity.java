package com.example.stimbot;

import com.example.stimbot.R;
import com.example.stimbot.SystemUiHider;
import com.example.stimbot.MyRenderer;

import android.support.v7.app.ActionBarActivity;
import android.annotation.TargetApi;
import android.opengl.GLSurfaceView;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.view.WindowManager;

public class StimbotActivity extends ActionBarActivity {
	static View rootView;

	private GLSurfaceView mView;
	private MyRenderer mRenderer;
	
	private SystemUiHider mSystemUiHider;

	//UI hiding parameters
	private static final boolean AUTO_HIDE = true;
	private static final int AUTO_HIDE_DELAY_MILLIS = 2000;
	private static final int HIDER_FLAGS = SystemUiHider.FLAG_HIDE_NAVIGATION;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);

		setContentView(R.layout.activity_stimbot);
		
		mView = (GLSurfaceView) findViewById(R.id.glview);
		mRenderer = new MyRenderer(this);
		mView.setRenderer(mRenderer);
		
		
        //The rest of this function is just code to hide all the Android UI crud (title bar, nav buttons, and top menu.)
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN); //disable menu at top
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); //don't let screen go dim
        mSystemUiHider = SystemUiHider.getInstance(this, mView, HIDER_FLAGS);
        mSystemUiHider.setup();
        
		
		mSystemUiHider
		.setOnVisibilityChangeListener(new SystemUiHider.OnVisibilityChangeListener() {
			@Override
			@TargetApi(Build.VERSION_CODES.HONEYCOMB_MR2)
			public void onVisibilityChange(boolean visible) {
				if (visible && AUTO_HIDE) {
					mHideHandler.removeCallbacks(mHideRunnable);
					mHideHandler.postDelayed(mHideRunnable, AUTO_HIDE_DELAY_MILLIS);
				}
			}
		});

		//OK, constructor done. Let's hide the controls immediately.
        hideCrap();
	}
		
	public void hideCrap() {
        getActionBar().hide(); //obliterate the stupid title menu thing
		mView.setSystemUiVisibility(View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.INVISIBLE);
		mSystemUiHider.hide();
    }

	Handler mHideHandler = new Handler();
	Runnable mHideRunnable = new Runnable() {
		@Override
		public void run() {
			mSystemUiHider.hide();
		}
	};

}

