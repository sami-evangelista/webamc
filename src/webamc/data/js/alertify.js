/**
 * configurate some stuff for alertify
 */
$(document).ready(function() {
    alertify.set('notifier', 'position', 'top-right');
    alertify.set('notifier', 'delay', 5);
    alertify.dialog('webamc_confirm', function factory (){
	return {
	    main: function (message, onok){
		this.setting('title', Lang['seq_confirmation_request']);
		this.setting('transition', 'fade');
		this.onok = onok;
		this.message = message;
                this.className = 'webamc_confirm';
	    },
	    setup: function(){
		return { 
		    buttons: [{
			text: Lang['name_yes'],
			className: 'yes-btn'
		    }, {
			text: Lang['name_no'],
			className: 'no-btn'
		    }],
		    options: {
			modal: true,
			resizeable: false,
			maximizable: false,
			closable: false
		    },
		    focus: {
			element: 1
		    }
		};
	    },
	    prepare: function(){
		this.setContent(this.message);
	    },
	    callback: function(closeEvent) {
		if (closeEvent.index == 0) {
		    this.onok();
		}
            },
            build: function(){
                this.elements.dialog.classList.add('webamc_confirm');
            },
	}});
    alertify.dialog('webamc_dialog', function factory (){
	return {
	    main: function (title, message, onyes, onno){
		this.setting('title', title);
		this.setting('transition', 'fade');
		this.onyes = onyes;
		this.message = message;
                this.className = 'webamc_confirm';
	    },
	    setup: function(){
		return { 
		    buttons: [{
			text: Lang['verb_validate'],
			className: 'yes-btn'
		    }, {
			text: Lang['verb_cancel'],
			className: 'no-btn'
		    }],
		    options: {
			modal: true,
			resizeable: true,
			maximizable: false,
			closable: false
		    },
		    focus: {
			element: 1
		    }
		};
	    },
	    prepare: function(){
		this.setContent(this.message);
	    },
	    callback: function(closeEvent) {
		if(closeEvent.index == 0) {
		    this.onyes(closeEvent);
		} else if(closeEvent.index == 0) {
		    this.onno(closeEvent);
		}
            },
            build: function(){
                this.elements.dialog.classList.add('webamc_confirm');
            },
	}});
});
