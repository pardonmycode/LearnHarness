extends Node2D

# Geschwindigkeit in Pixeln pro Sekunde.
@export var speed: float = 200.0

func _process(delta: float) -> void:
	# X ist die waagerechte Achse. Ein positiver Wert bewegt nach rechts.
	position.x += speed * delta
