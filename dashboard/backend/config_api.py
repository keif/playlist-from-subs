"""
Configuration API Blueprint

Provides REST API endpoints for configuration management.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from flask import Blueprint, jsonify, request

from config_manager import ConfigManager

logger = logging.getLogger(__name__)

# Create blueprint
config_bp = Blueprint('config', __name__, url_prefix='/api/config')

# Initialize config manager
config_manager = ConfigManager()


@config_bp.route('', methods=['GET'])
def get_config():
    """
    Get current configuration.

    Returns:
        JSON response with current configuration
    """
    try:
        config = config_manager.load_config()
        return jsonify({
            'success': True,
            'config': config,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.exception("Error getting config")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@config_bp.route('', methods=['PUT'])
def update_config():
    """
    Update configuration.

    Expects JSON body with configuration values to update.

    Returns:
        JSON response with success status and updated config
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400

        updates = request.get_json()

        # Update configuration
        result = config_manager.update_config(updates)

        if result['success']:
            return jsonify({
                'success': True,
                'config': result['config'],
                'message': 'Configuration updated successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'errors': result['errors'],
                'timestamp': datetime.now().isoformat()
            }), 400

    except Exception as e:
        logger.exception("Error updating config")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@config_bp.route('/validate', methods=['POST'])
def validate_config():
    """
    Validate configuration without saving.

    Expects JSON body with configuration to validate.

    Returns:
        JSON response with validation result
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400

        config = request.get_json()
        validation_result = config_manager.validate_config(config)

        return jsonify({
            'valid': validation_result['valid'],
            'errors': validation_result['errors'],
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.exception("Error validating config")
        return jsonify({
            'valid': False,
            'errors': [str(e)],
            'timestamp': datetime.now().isoformat()
        }), 500


@config_bp.route('/defaults', methods=['GET'])
def get_defaults():
    """
    Get default configuration values.

    Returns:
        JSON response with default configuration
    """
    try:
        defaults = config_manager.get_defaults()
        return jsonify({
            'success': True,
            'defaults': defaults,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.exception("Error getting defaults")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@config_bp.route('/reset', methods=['POST'])
def reset_config():
    """
    Reset configuration to defaults.

    Returns:
        JSON response with success status
    """
    try:
        success = config_manager.reset_to_defaults()

        if success:
            return jsonify({
                'success': True,
                'message': 'Configuration reset to defaults',
                'config': config_manager.get_defaults(),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to reset configuration',
                'timestamp': datetime.now().isoformat()
            }), 500

    except Exception as e:
        logger.exception("Error resetting config")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@config_bp.route('/summary', methods=['GET'])
def get_config_summary():
    """
    Get configuration summary with organized sections.

    Returns:
        JSON response with config summary
    """
    try:
        summary = config_manager.get_config_summary()
        return jsonify({
            'success': True,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.exception("Error getting config summary")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
