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
});
