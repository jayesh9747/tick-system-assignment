from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from .models import Broker, Script, Ticks
import logging
from datetime import datetime

logger = logging.getLogger('tick_consumer')


@shared_task
def get_broker(broker_id):
    """
    Synchronously fetch broker details with all linked scripts and api_config.

    Args:
        broker_id (int): The ID of the broker to fetch

    Returns:
        dict: Broker details including scripts and api_config

    Raises:
        ObjectDoesNotExist: If broker not found
    """
    try:
        broker = Broker.objects.prefetch_related('scripts').get(id=broker_id)

        result = {
            'id': broker.id,
            'type': broker.type,
            'name': broker.name,
            'api_config': broker.api_config,
            'scripts': [
                {
                    'id': script.id,
                    'name': script.name,
                    'trading_symbol': script.trading_symbol,
                    'additional_data': script.additional_data,
                }
                for script in broker.scripts.all()
            ]
        }

        logger.info(f"Fetched broker {broker_id}: {broker.name} with {len(result['scripts'])} scripts")
        return result

    except ObjectDoesNotExist:
        logger.error(f"Broker with ID {broker_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error fetching broker {broker_id}: {str(e)}", exc_info=True)
        raise


@shared_task
def consume_tick(tick_data):
    """
    Bulk save tick data to MySQL database.

    Args:
        tick_data (list[dict]): List of tick dictionaries with format:
            {
                'script_id': int,
                'tick_value': str/float/Decimal,
                'volume': str/float/Decimal or None,
                'received_at_producer': datetime or ISO string
            }

    Returns:
        dict: Status with count of saved ticks
    """
    try:
        if not tick_data:
            logger.warning("Empty tick_data received")
            return {'status': 'success', 'count': 0}

        # Ensure tick_data is a list
        if isinstance(tick_data, dict):
            tick_data = [tick_data]

        tick_objects = []
        for tick in tick_data:
            # Parse datetime if it's a string
            received_at = tick['received_at_producer']
            if isinstance(received_at, str):
                received_at = datetime.fromisoformat(received_at.replace('Z', '+00:00'))

            tick_obj = Ticks(
                script_id=tick['script_id'],
                tick_value=tick['tick_value'],
                volume=tick.get('volume'),
                received_at_producer=received_at
            )
            tick_objects.append(tick_obj)

        # Bulk create for performance
        Ticks.objects.bulk_create(tick_objects, batch_size=1000)

        logger.info(f"Successfully saved {len(tick_objects)} ticks")
        return {'status': 'success', 'count': len(tick_objects)}

    except Exception as e:
        logger.error(f"Error consuming ticks: {str(e)}", exc_info=True)
        raise
