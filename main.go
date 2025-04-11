package main

/*
Go version of the original package
*/
import (
	"os"

	"github.com/gin-gonic/gin"
	"github.com/hashicorp/mdns"
)

const (
	SERVICENAME = "alterlog"
)

func main() {

	useMDNS := false
	if useMDNS { // TODO make this real and not an example service
		host, _ := os.Hostname()
		info := []string{"My awesome service"}
		service, _ := mdns.NewMDNSService(host, "_foobar._tcp", "", "", 8000, nil, info)

		// Create the mDNS server, defer shutdown
		server, _ := mdns.NewServer(&mdns.Config{Zone: service})
		defer server.Shutdown()
	}

	r := gin.Default()

	//r.GET("/api/pathname",function)

	r.Run()

}
